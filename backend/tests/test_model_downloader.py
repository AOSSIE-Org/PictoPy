"""Tests for app.utils.model_downloader.ensure_model.

These spin up a local HTTP server that can serve a model fully, close the
connection partway through, or honour Range requests, so the download,
resume, interruption and verification paths are exercised without the network.

Regression cover for the bug where an interrupted download was written
straight to the model's final path, so GET /models/status and the SigLIP2
loaders reported a half-written file as installed and then failed to load it.
"""

import asyncio
import hashlib
import http.server
import os
import threading
from pathlib import Path
from typing import Callable, Optional

import httpx
import pytest

from app.utils import model_downloader
from app.utils.model_downloader import PART_SUFFIX, ensure_model

ProgressCallback = Optional[Callable[[float, int, int], None]]

MODEL_KEY = "test_model"
BODY = b"".join(bytes([i % 256]) for i in range(256)) * 4096  # 1 MiB, deterministic
BODY_SHA256 = hashlib.sha256(BODY).hexdigest()


class _FullHandler(http.server.BaseHTTPRequestHandler):
    """Serves the whole body, honouring a Range header with a 206 so resume
    continues from the bytes already on disk."""

    def do_GET(self) -> None:
        range_header = self.headers.get("Range")
        start = 0
        if range_header and range_header.startswith("bytes="):
            start = int(range_header.split("=", 1)[1].split("-", 1)[0])
        if start >= len(BODY):
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{len(BODY)}")
            self.end_headers()
            return
        chunk = BODY[start:]
        self.send_response(206 if start > 0 else 200)
        self.send_header("Content-Length", str(len(chunk)))
        if start > 0:
            self.send_header(
                "Content-Range", f"bytes {start}-{len(BODY) - 1}/{len(BODY)}"
            )
        self.end_headers()
        self.wfile.write(chunk)

    def log_message(self, *args: object) -> None:
        pass


class _EarlyCloseHandler(http.server.BaseHTTPRequestHandler):
    """Announces the full length but writes only the first 64 KiB then drops the
    connection, which raises httpx.RemoteProtocolError on the client."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY[: 64 * 1024])
        self.close_connection = True

    def log_message(self, *args: object) -> None:
        pass


def _serve(
    handler: type[http.server.BaseHTTPRequestHandler],
) -> http.server.ThreadingHTTPServer:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


@pytest.fixture
def model_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Point the downloader at a temp file and a registry entry we control.
    Returns the final model path; the per-test server fills in the url."""
    final_path = str(tmp_path / "TestModel.bin")
    monkeypatch.setitem(
        model_downloader.MODEL_REGISTRY,
        MODEL_KEY,
        {
            "filename": "TestModel.bin",
            "url": "",  # set by each test to its server address
            "sha256": BODY_SHA256,
            "size_mb": 1,
            "feature": "object_detection",
            "tier": "nano",
        },
    )
    monkeypatch.setattr(model_downloader, "get_model_path", lambda key: final_path)
    return final_path


def _set_url(url: str) -> None:
    model_downloader.MODEL_REGISTRY[MODEL_KEY]["url"] = url


def test_successful_download_installs_and_verifies(model_env: str) -> None:
    server = _serve(_FullHandler)
    _set_url(f"http://127.0.0.1:{server.server_port}/m")
    try:
        path = asyncio.run(ensure_model(MODEL_KEY))
    finally:
        server.shutdown()

    assert path == model_env
    assert os.path.exists(model_env)
    with open(model_env, "rb") as f:
        assert f.read() == BODY
    # The .part scratch file is renamed away on success.
    assert not os.path.exists(model_env + PART_SUFFIX)


def test_interrupted_download_is_not_reported_as_installed(model_env: str) -> None:
    server = _serve(_EarlyCloseHandler)
    _set_url(f"http://127.0.0.1:{server.server_port}/m")
    try:
        with pytest.raises(RuntimeError):
            asyncio.run(ensure_model(MODEL_KEY, max_retries=1))
    finally:
        server.shutdown()

    # The core regression: the final path must not exist after an interruption,
    # so os.path.exists()-based status and loaders see it as not installed.
    assert not os.path.exists(model_env)
    # The partial bytes are kept under .part so a later attempt can resume.
    assert os.path.exists(model_env + PART_SUFFIX)
    assert os.path.getsize(model_env + PART_SUFFIX) == 64 * 1024


def test_remote_protocol_error_is_retried(model_env: str) -> None:
    """First attempt drops the connection; the second serves the rest. The old
    code did not catch RemoteProtocolError, so the first drop ended it."""
    early = _serve(_EarlyCloseHandler)
    full = _serve(_FullHandler)

    port_box = {"port": early.server_port}
    original = model_downloader._download_to_part

    async def flaky_then_full(
        client: httpx.AsyncClient,
        url: str,
        part_path: str,
        cb: ProgressCallback,
    ) -> None:
        # Swap to the good server after the first (failing) attempt.
        url = f"http://127.0.0.1:{port_box['port']}/m"
        port_box["port"] = full.server_port
        return await original(client, url, part_path, cb)

    _set_url(f"http://127.0.0.1:{early.server_port}/m")
    try:
        model_downloader._download_to_part = flaky_then_full
        path = asyncio.run(ensure_model(MODEL_KEY, max_retries=2))
    finally:
        model_downloader._download_to_part = original
        early.shutdown()
        full.shutdown()

    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read() == BODY
    assert not os.path.exists(model_env + PART_SUFFIX)


def test_resume_continues_from_partial_file(model_env: str) -> None:
    """A leftover .part from an earlier interrupted run is resumed, not
    restarted: the Range-aware server only sends the remaining bytes."""
    part_path = model_env + PART_SUFFIX
    with open(part_path, "wb") as f:
        f.write(BODY[: 64 * 1024])

    server = _serve(_FullHandler)
    _set_url(f"http://127.0.0.1:{server.server_port}/m")
    try:
        path = asyncio.run(ensure_model(MODEL_KEY))
    finally:
        server.shutdown()

    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read() == BODY
    assert not os.path.exists(part_path)


def test_stale_oversized_partial_file_is_discarded_on_416(model_env: str) -> None:
    """A .part larger than the remote file gets a 416 for its Range request; it
    is discarded and the model is fetched fresh rather than looping."""
    part_path = model_env + PART_SUFFIX
    with open(part_path, "wb") as f:
        f.write(BODY + b"stale")

    server = _serve(_FullHandler)
    _set_url(f"http://127.0.0.1:{server.server_port}/m")
    try:
        path = asyncio.run(ensure_model(MODEL_KEY))
    finally:
        server.shutdown()

    with open(path, "rb") as f:
        assert f.read() == BODY
    assert not os.path.exists(part_path)


def test_hash_mismatch_is_rejected(model_env: str) -> None:
    model_downloader.MODEL_REGISTRY[MODEL_KEY]["sha256"] = "0" * 64
    server = _serve(_FullHandler)
    _set_url(f"http://127.0.0.1:{server.server_port}/m")
    try:
        with pytest.raises(RuntimeError):
            asyncio.run(ensure_model(MODEL_KEY, max_retries=1))
    finally:
        server.shutdown()

    # A model that fails verification is never installed and its .part is cleaned up.
    assert not os.path.exists(model_env)
    assert not os.path.exists(model_env + PART_SUFFIX)
