from __future__ import annotations

import threading

_active_sessions: dict[str, int] = {}
_models_pending_deletion: set[str] = set()
_registry_lock = threading.RLock()


def mark_model_session_active(model_key: str) -> None:
    with _registry_lock:
        if model_key in _models_pending_deletion:
            raise RuntimeError(
                f"Model '{model_key}' is being deleted; cannot start a new session."
            )
        _active_sessions[model_key] = _active_sessions.get(model_key, 0) + 1


def mark_model_session_inactive(model_key: str) -> None:
    with _registry_lock:
        count = _active_sessions.get(model_key, 0)
        if count <= 1:
            _active_sessions.pop(model_key, None)
            return
        _active_sessions[model_key] = count - 1


def get_active_session_count(model_key: str) -> int:
    with _registry_lock:
        return _active_sessions.get(model_key, 0)


def try_mark_model_for_deletion(model_key: str) -> int | None:
    with _registry_lock:
        count = _active_sessions.get(model_key, 0)
        if count > 0:
            return count
        _models_pending_deletion.add(model_key)
        return None


def release_model_deletion_mark(model_key: str) -> None:
    with _registry_lock:
        _models_pending_deletion.discard(model_key)
