import os
import hashlib
import logging
import asyncio
from pathlib import Path
from typing import Optional, Callable
import httpx
from app.models.model_registry import MODEL_REGISTRY, get_model_path

logger = logging.getLogger(__name__)

# Suffix for the in-progress download. The model is streamed here and only
# renamed onto its final path once its SHA-256 matches, so every other part of
# the app (GET /models/status and the SigLIP2 loaders) that checks the final
# path with os.path.exists() never sees a half-written file as "installed".
PART_SUFFIX = ".part"

# Exceptions worth retrying: httpx.TransportError is the base class for
# timeouts, network errors and protocol errors (including RemoteProtocolError,
# raised when a server closes the connection mid-response). HTTPStatusError
# covers transient 5xx responses raised by raise_for_status().
RETRYABLE_EXCEPTIONS = (httpx.TransportError, httpx.HTTPStatusError)


async def verify_sha256(file_path: str, expected_sha256: str) -> bool:
    """Verify the SHA-256 checksum of a file."""

    def _compute() -> bool:
        if not os.path.exists(file_path):
            return False

        sha256_hash = hashlib.sha256()
        # Read file in 4MB chunks to limit memory footprint
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096 * 1024), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest() == expected_sha256

    return await asyncio.to_thread(_compute)


async def _download_to_part(
    client: httpx.AsyncClient,
    url: str,
    part_path: str,
    progress_callback: Optional[Callable[[float, int, int], None]],
) -> None:
    """Stream ``url`` into ``part_path``, resuming from whatever bytes are
    already there with an HTTP Range request. A 416 (range not satisfiable)
    means the partial file is stale, so it is discarded and fetched fresh."""
    existing_size = os.path.getsize(part_path) if os.path.exists(part_path) else 0
    headers = {}
    if existing_size > 0:
        headers["Range"] = f"bytes={existing_size}-"

    async with client.stream("GET", url, headers=headers) as response:
        if response.status_code == 416:
            logger.warning(
                "Range not satisfiable for %s; discarding partial file and "
                "restarting the download.",
                part_path,
            )
            await response.aclose()
            if os.path.exists(part_path):
                os.remove(part_path)
            await _download_to_part(client, url, part_path, progress_callback)
            return

        response.raise_for_status()

        # A 206 means the server honoured the Range header, so we append;
        # anything else (200) is a full body, so we overwrite from scratch.
        resuming = response.status_code == 206
        mode = "ab" if resuming else "wb"
        content_length = int(response.headers.get("Content-Length", 0))
        if resuming:
            total_size = content_length + existing_size
            downloaded = existing_size
        else:
            total_size = content_length
            downloaded = 0

        with open(part_path, mode) as f:
            async for chunk in response.aiter_bytes(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total_size > 0:
                    percent = min((downloaded / total_size) * 100, 100.0)
                    progress_callback(percent, downloaded, total_size)


async def ensure_model(
    model_key: str,
    max_retries: int = 3,
    progress_callback: Optional[Callable[[float, int, int], None]] = None,
) -> str:
    """
    Ensure a model is present on disk and valid.
    Downloads it if missing or corrupted, resuming interrupted downloads.
    Returns the path to the model.

    The download is written to a ``<model>.part`` file and only renamed onto
    the final path after its SHA-256 matches, so an interrupted download is
    never reported as installed and never loaded.
    """
    if model_key not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model key: {model_key}")

    spec = MODEL_REGISTRY[model_key]
    model_path = get_model_path(model_key)
    part_path = model_path + PART_SUFFIX
    expected_sha256 = spec["sha256"]
    url = spec["url"]

    # Fast path: a verified final file is already in place.
    if os.path.exists(model_path):
        if await verify_sha256(model_path, expected_sha256):
            logger.info(f"Model {model_key} is already present and verified.")
            return model_path
        else:
            logger.warning(
                f"Model {model_key} exists but is corrupted. Re-downloading."
            )
            os.remove(model_path)

    Path(model_path).parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, max_retries + 1):
        try:
            existing_size = (
                os.path.getsize(part_path) if os.path.exists(part_path) else 0
            )
            logger.info(
                f"Downloading {model_key} from {url} "
                f"(Attempt {attempt}/{max_retries}, offset {existing_size})..."
            )

            timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=timeout
            ) as client:
                await _download_to_part(client, url, part_path, progress_callback)

            # Verify the completed .part file before moving it into place.
            if await verify_sha256(part_path, expected_sha256):
                # Atomic rename within the same directory: the final path only
                # ever appears once the file is complete and verified.
                os.replace(part_path, model_path)
                logger.info(f"Model {model_key} successfully downloaded and verified.")
                return model_path
            else:
                logger.error(
                    f"Hash mismatch for downloaded model {model_key}. "
                    "Discarding partial file."
                )
                if os.path.exists(part_path):
                    os.remove(part_path)
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)

        except RETRYABLE_EXCEPTIONS as e:
            logger.warning(
                f"Download attempt {attempt}/{max_retries} failed for "
                f"{model_key}: {type(e).__name__}: {e}"
            )
            if attempt == max_retries:
                raise RuntimeError(
                    f"Failed to download and verify model {model_key} "
                    f"after {max_retries} attempts."
                ) from e
            await asyncio.sleep(2**attempt)

    raise RuntimeError(
        f"Failed to download and verify model {model_key} after {max_retries} attempts."
    )
