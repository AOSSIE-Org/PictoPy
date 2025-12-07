let ws: WebSocket | null = null;
let reconnectTimer: number | null = null;
let backoff = 1000;
const MAX_BACKOFF = 30_000;

export type WsListener = (msg: any) => void;
const listeners = new Set<WsListener>();

const WS_URL = 'ws://localhost:8000/ws';

function connect() {
  if (ws) return;

  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.debug('[WS] connected');
    backoff = 1000;
  };

  ws.onmessage = (ev) => {
    try {
      const parsed = JSON.parse(ev.data);
      listeners.forEach((fn) => fn(parsed));
    } catch (e) {
      console.error('[WS] parse error', e);
    }
  };

  ws.onclose = () => {
    ws = null;
    scheduleReconnect();
  };

  ws.onerror = (err) => {
    console.error('[WS] error', err);
    try {
      ws?.close();
    } catch {}
  };
}

function scheduleReconnect() {
  if (reconnectTimer) return;

  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    backoff = Math.min(backoff * 2, MAX_BACKOFF);
    connect();
  }, backoff);
}

/* ---------- PUBLIC API ---------- */

export function startWebSocket() {
  connect();
}

export function addWsListener(fn: WsListener) {
  listeners.add(fn);
  connect();
  return () => listeners.delete(fn);
}

export function wsSend(obj: unknown) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(obj));
  }
}
