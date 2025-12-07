# ws_manager.py
import asyncio
import json
import time
import threading
from typing import Dict, Any, Set, Optional
from starlette.websockets import WebSocket

# --- connection tracking ---
_active_connections: Set[WebSocket] = set()
_conn_lock = asyncio.Lock()

# monotonic sequence (thread-safe)
_seq = 0
_seq_lock = threading.Lock()


def next_seq() -> int:
    global _seq
    with _seq_lock:
        _seq += 1
        return _seq


# recent events for replay
_RECENT_MAX = 1000
_recent_events = []  # list of dicts: {"seq":..., "type":..., "ts":..., "payload":...}

# event queue & loop handle (populated on startup)
_EVENT_QUEUE_MAXSIZE = 1024
_event_queue: Optional[asyncio.Queue] = None
_main_loop: Optional[asyncio.AbstractEventLoop] = None

# throttling / coalescing (simple)
_last_sent_per_job: Dict[
    str, Dict[str, Any]
] = {}  # job_id -> {"percent": int, "ts": float}
_pending_latest_per_job: Dict[str, Dict[str, Any]] = {}  # job_id -> latest payload

# tuning
_PERCENT_DELTA = 1  # percent change threshold
_MIN_INTERVAL = 0.25  # minimum seconds between sends for same job
_FLUSH_INTERVAL = 0.5  # flush pending coalesced messages every X seconds

# background tasks
_sender_task: Optional[asyncio.Task] = None
_flusher_task: Optional[asyncio.Task] = None

# simple metric
_dropped_count = 0

# -----------------------
# Public API for the app
# -----------------------


async def register_ws(ws):
    """Register incoming WebSocket connection (ws is a Starlette/FastAPI WebSocket)."""
    await ws.accept()
    async with _conn_lock:
        _active_connections.add(ws)


async def unregister_ws(ws):
    async with _conn_lock:
        _active_connections.discard(ws)
    try:
        await ws.close()
    except Exception:
        pass


def get_events_since(seq: Optional[int]):
    """Return list of events with seq > given seq (seq may be None to get all)."""
    if seq is None:
        return _recent_events.copy()
    return [e for e in _recent_events if e["seq"] > seq]


async def replay_events(ws, since_seq: Optional[int] = None):
    """Replay recent events to a WebSocket since `since_seq`."""
    events = get_events_since(since_seq)
    if not events:
        return
    for ev in events:
        try:
            await ws.send_text(json.dumps(ev))
        except Exception:
            break


def publish_progress_from_thread(payload: Dict[str, Any]):
    """
    Called from blocking threads (worker). Non-blocking.
    Payload must include at least: {"job_id": str, "percent": int, "status": str}
    If the internal queue is full the message is dropped.
    """
    global _dropped_count, _main_loop, _event_queue

    if _main_loop is None:
        # manager not started; drop (or optionally buffer)
        _dropped_count += 1
        return

    def _enqueue():
        global _event_queue, _dropped_count
        if _event_queue is None:
            _event_queue = asyncio.Queue(maxsize=_EVENT_QUEUE_MAXSIZE)
        try:
            _event_queue.put_nowait(payload)
        except asyncio.QueueFull:
            _dropped_count += 1

    # schedule enqueue on main loop thread
    _main_loop.call_soon_threadsafe(_enqueue)


async def start_ws_manager_background_tasks(
    loop: Optional[asyncio.AbstractEventLoop] = None,
):
    """
    Call this on FastAPI startup (from the event loop) to initialize the queue
    and start background sender + flusher tasks.
    """
    print("Starting WebSocket manager background tasks...")
    global _event_queue, _sender_task, _flusher_task, _main_loop
    if loop is None:
        loop = asyncio.get_running_loop()
    _main_loop = loop

    # Initialize queue FIRST
    _event_queue = asyncio.Queue(maxsize=_EVENT_QUEUE_MAXSIZE)

    # start background tasks if not already running
    if _sender_task is None or _sender_task.done():
        _sender_task = asyncio.create_task(_sender_loop())
    if _flusher_task is None or _flusher_task.done():
        _flusher_task = asyncio.create_task(_periodic_flusher())


# -----------------------
# Internal helpers
# -----------------------


def _format_and_persist(
    event_type: str, payload: Dict[str, Any], persist_event: bool = True
) -> str:
    msg = {
        "type": event_type,
        "seq": next_seq(),
        "ts": int(time.time() * 1000),
        "payload": payload,
    }
    if persist_event:
        _recent_events.append(msg)
        if len(_recent_events) > _RECENT_MAX:
            _recent_events.pop(0)
    return json.dumps(msg)


async def _broadcast_to_all_connections(text: str):
    """Broadcast message to all connected WebSocket clients."""
    stale = []
    async with _conn_lock:
        to_iter = list(_active_connections)
    for ws in to_iter:
        try:
            await ws.send_text(text)
        except Exception:
            stale.append(ws)
    if stale:
        async with _conn_lock:
            for s in stale:
                _active_connections.discard(s)


async def _sender_loop():
    global _event_queue, _last_sent_per_job, _pending_latest_per_job
    if _event_queue is None:
        _event_queue = asyncio.Queue(maxsize=_EVENT_QUEUE_MAXSIZE)

    while True:
        try:
            payload = await _event_queue.get()
        except asyncio.CancelledError:
            break

        job_id = (
            str(payload.get("job_id")) if payload.get("job_id") is not None else None
        )
        percent = payload.get("percent")
        status = payload.get("status")

        should_send_immediately = False
        if status in ("done", "failed", "cancelled"):
            should_send_immediately = True
        else:
            last = _last_sent_per_job.get(job_id)
            now = time.time()
            if last is None:
                should_send_immediately = True
            else:
                last_percent = last.get("percent")
                last_ts = last.get("ts", 0)
                if percent is None:
                    should_send_immediately = True
                elif abs(percent - (last_percent or 0)) >= _PERCENT_DELTA:
                    should_send_immediately = True
                elif (now - last_ts) >= _MIN_INTERVAL:
                    should_send_immediately = True

        if should_send_immediately:
            text = _format_and_persist("progress", payload, persist_event=True)
            await _broadcast_to_all_connections(text)
            _last_sent_per_job[job_id] = {"percent": percent, "ts": time.time()}
        else:
            # coalesce: keep latest payload for the job
            _pending_latest_per_job[job_id] = payload

        # micro-batch: try to drain a few more quickly
        for _ in range(8):
            if _event_queue.empty():
                break
            try:
                payload = _event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            job_id = (
                str(payload.get("job_id"))
                if payload.get("job_id") is not None
                else None
            )
            percent = payload.get("percent")
            status = payload.get("status")

            should_send_immediately = False
            if status in ("done", "failed", "cancelled"):
                should_send_immediately = True
            else:
                last = _last_sent_per_job.get(job_id)
                now = time.time()
                if last is None:
                    should_send_immediately = True
                else:
                    last_percent = last.get("percent")
                    last_ts = last.get("ts", 0)
                    if percent is None:
                        should_send_immediately = True
                    elif abs(percent - (last_percent or 0)) >= _PERCENT_DELTA:
                        should_send_immediately = True
                    elif (now - last_ts) >= _MIN_INTERVAL:
                        should_send_immediately = True

            if should_send_immediately:
                text = _format_and_persist("progress", payload, persist_event=True)
                await _broadcast_to_all_connections(text)
                _last_sent_per_job[job_id] = {"percent": percent, "ts": time.time()}
            else:
                _pending_latest_per_job[job_id] = payload


async def _periodic_flusher():
    global _pending_latest_per_job, _last_sent_per_job
    while True:
        try:
            await asyncio.sleep(_FLUSH_INTERVAL)
        except asyncio.CancelledError:
            break
        if not _pending_latest_per_job:
            continue
        to_flush = dict(_pending_latest_per_job)
        _pending_latest_per_job.clear()
        for job_id, payload in to_flush.items():
            text = _format_and_persist("progress", payload, persist_event=True)
            await _broadcast_to_all_connections(text)
            percent = payload.get("percent")
            _last_sent_per_job[job_id] = {"percent": percent, "ts": time.time()}
