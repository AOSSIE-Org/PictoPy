import os
import hashlib
import logging
import asyncio
from pathlib import Path
from typing import Optional, Callable
import httpx
from app.models.model_registry import MODEL_REGISTRY, get_model_path

logger = logging.getLogger(__name__)


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


async def ensure_model(
    model_key: str,
    max_retries: int = 3,
    progress_callback: Optional[Callable[[float, int, int], None]] = None,
) -> str:
    """
    Ensure a model is present on disk and valid.
    Downloads it if missing or corrupted with range resumability.
    Returns the path to the model.
    """
    if model_key not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model key: {model_key}")

    spec = MODEL_REGISTRY[model_key]
    model_path = get_model_path(model_key)
    expected_sha256 = spec["sha256"]
    url = spec["url"]

    # Fast path: check if valid file already exists
    if os.path.exists(model_path):
        if await verify_sha256(model_path, expected_sha256):
            logger.info(f"Model {model_key} is already present and verified.")
            return model_path
        else:
            logger.warning(
                f"Model {model_key} exists but is corrupted or incomplete. Attempting resume..."
            )
            # Do NOT delete the file here; we will try to resume the download

    Path(model_path).parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, max_retries + 1):
        try:
            existing_size = (
                os.path.getsize(model_path) if os.path.exists(model_path) else 0
            )
            headers = {}
            if existing_size > 0:
                headers["Range"] = f"bytes={existing_size}-"

            logger.info(
                f"Downloading {model_key} from {url} (Attempt {attempt}/{max_retries}, offset {existing_size})..."
            )

            timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)
            retry_full_after_416 = False
            async with httpx.AsyncClient(
                follow_redirects=True, timeout=timeout
            ) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    if response.status_code == 416:
                        logger.warning(
                            "Range not satisfiable for %s. Restarting with full download after closing stream.",
                            model_key,
                        )
                        retry_full_after_416 = True
                    else:
                        response.raise_for_status()
                        mode = "ab" if response.status_code == 206 else "wb"
                        content_length = int(response.headers.get("Content-Length", 0))
                        if mode == "ab":
                            total_size = content_length + existing_size
                            downloaded = existing_size
                        else:
                            total_size = content_length
                            downloaded = 0

                        with open(model_path, mode) as f:
                            async for chunk in response.aiter_bytes(chunk_size=65536):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if progress_callback and total_size > 0:
                                    percent = min(
                                        (downloaded / total_size) * 100, 100.0
                                    )
                                    progress_callback(percent, downloaded, total_size)

                if retry_full_after_416:
                    if os.path.exists(model_path):
                        os.remove(model_path)
                    async with client.stream("GET", url) as fresh_response:
                        fresh_response.raise_for_status()
                        content_length = int(
                            fresh_response.headers.get("Content-Length", 0)
                        )
                        total_size = content_length
                        downloaded = 0
                        with open(model_path, "wb") as f:
                            async for chunk in fresh_response.aiter_bytes(
                                chunk_size=65536
                            ):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if progress_callback and total_size > 0:
                                    percent = min(
                                        (downloaded / total_size) * 100, 100.0
                                    )
                                    progress_callback(percent, downloaded, total_size)

            # Post-download verification
            if await verify_sha256(model_path, expected_sha256):
                logger.info(f"Model {model_key} successfully downloaded and verified.")
                return model_path
            else:
                logger.error(
                    f"Hash mismatch for downloaded model {model_key}. File corrupted."
                )
                if os.path.exists(model_path):
                    os.remove(model_path)
                if attempt < max_retries:
                    await asyncio.sleep(2**attempt)

        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
            logger.warning(
                f"Download attempt {attempt}/{max_retries} failed for {model_key}: {e}"
            )
            if attempt == max_retries:
                raise RuntimeError(
                    f"Failed to download and verify model {model_key} after {max_retries} attempts."
                ) from e
            await asyncio.sleep(2**attempt)

    raise RuntimeError(
        f"Failed to download and verify model {model_key} after {max_retries} attempts."
    )
