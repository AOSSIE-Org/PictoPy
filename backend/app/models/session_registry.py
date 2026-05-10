from __future__ import annotations

import threading

_active_sessions: dict[str, int] = {}
_registry_lock = threading.Lock()


def mark_model_session_active(model_key: str) -> None:
    with _registry_lock:
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
