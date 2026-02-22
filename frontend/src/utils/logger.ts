import {
  debug as tauriDebug,
  info as tauriInfo,
  warn as tauriWarn,
  error as tauriError,
  trace as tauriTrace,
} from '@tauri-apps/plugin-log';
import { isTauriEnvironment } from '@/utils/tauriUtils';

/**
 * Logger utility that routes logs through Tauri's native logging plugin.
 *
 * In Tauri: logs are written to the app's log file and are NOT exposed
 * in the browser console (solving the privacy concern).
 *
 * In browser (dev without Tauri): falls back to console methods so
 * developers can still see output during web-only development.
 */

function safeStringify(obj: unknown): string {
  const seen = new WeakSet();
  try {
    return JSON.stringify(
      obj,
      (_key, value) => {
        if (typeof value === 'object' && value !== null) {
          if (seen.has(value)) return '[Circular]';
          seen.add(value);
        }
        return value;
      },
      2,
    );
  } catch {
    return String(obj);
  }
}

function stringify(...args: unknown[]): string {
  return args
    .map((arg) => {
      if (arg instanceof Error) {
        const extras: Record<string, unknown> = {};
        const errorRecord = arg as unknown as Record<string, unknown>;
        for (const key of Object.keys(arg)) {
          extras[key] = errorRecord[key];
        }
        return safeStringify({
          name: arg.name,
          message: arg.message,
          stack: arg.stack,
          ...extras,
        });
      }
      return typeof arg === 'object' && arg !== null
        ? safeStringify(arg)
        : String(arg);
    })
    .join(' ');
}

const logger = {
  trace(...args: unknown[]) {
    if (isTauriEnvironment()) {
      tauriTrace(stringify(...args));
    } else {
      console.debug('[TRACE]', ...args);
    }
  },

  debug(...args: unknown[]) {
    if (isTauriEnvironment()) {
      tauriDebug(stringify(...args));
    } else {
      console.debug(...args);
    }
  },

  info(...args: unknown[]) {
    if (isTauriEnvironment()) {
      tauriInfo(stringify(...args));
    } else {
      console.info(...args);
    }
  },

  warn(...args: unknown[]) {
    if (isTauriEnvironment()) {
      tauriWarn(stringify(...args));
    } else {
      console.warn(...args);
    }
  },

  error(...args: unknown[]) {
    if (isTauriEnvironment()) {
      tauriError(stringify(...args));
    } else {
      console.error(...args);
    }
  },

  /** Alias for info — drop-in replacement for console.log */
  log(...args: unknown[]) {
    this.info(...args);
  },
};

export default logger;
