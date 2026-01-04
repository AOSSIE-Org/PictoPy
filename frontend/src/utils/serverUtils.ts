import { Command } from '@tauri-apps/plugin-shell';
import { invoke } from '@tauri-apps/api/core';
import { BACKEND_URL } from '@/config/Backend.ts';

const SHUTDOWN_TIMEOUT_MS = 5000;
const SHUTDOWN_RECHECK_DELAY_MS = 1000;

// Prevent race conditions between triggerShutdown and stopServer
let shutdownInProgress = false;

const isWindows = (): boolean => {
  return navigator.userAgent.toLowerCase().includes('windows');
};

const TAURI_READY_TIMEOUT_MS = 5000;
const TAURI_READY_CHECK_INTERVAL_MS = 100;

const waitForTauriReady = async (): Promise<boolean> => {
  const startTime = Date.now();

  while (Date.now() - startTime < TAURI_READY_TIMEOUT_MS) {
    if (
      typeof window !== 'undefined' &&
      '__TAURI_INTERNALS__' in window &&
      window.__TAURI_INTERNALS__ !== undefined
    ) {
      // Small delay to ensure plugins are also initialized
      await new Promise((resolve) => setTimeout(resolve, 50));
      return true;
    }
    await new Promise((resolve) =>
      setTimeout(resolve, TAURI_READY_CHECK_INTERVAL_MS),
    );
  }

  console.warn('Tauri readiness check timed out');
  return false;
};

const isServerRunning = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${BACKEND_URL}/health`);
    if (response.ok) {
      return true;
    } else {
      return false;
    }
  } catch (error) {
    console.error('Error checking server status:', error);
    return false;
  }
};

export const startServer = async () => {
  try {
    // Wait for Tauri to be fully ready (fixes Linux initialization race)
    const tauriReady = await waitForTauriReady();
    if (!tauriReady) {
      console.error('Tauri not ready, cannot start server');
      return;
    }

    if (!(await isServerRunning())) {
      const serverPath: string = await invoke('get_server_path');
      const command = Command.create(
        isWindows() ? 'StartServerWindows' : 'StartServerUnix',
        '',
        { cwd: serverPath },
      );

      const child = await command.spawn();
      command.stderr.on('data', (line) => console.error('Error:', line));
      console.log('PictoPy Server started with PID:', child.pid);
    }
  } catch (error) {
    console.error('Error starting server:', error);
  }
};

// Fire-and-forget shutdown trigger.
export const triggerShutdown = (): void => {
  if (shutdownInProgress) {
    console.log('Shutdown already in progress, skipping...');
    return;
  }
  shutdownInProgress = true;
  console.log('Initialized backend shutdown...');

  // Always call forceKillServer as backup - it will kill both Server and Sync
  // This is belt-and-suspenders: HTTP shutdown + process kill
  forceKillServer().catch((err) =>
    console.error('Force kill during shutdown:', err),
  );

  fetch(`${BACKEND_URL}/shutdown`, {
    method: 'POST',
    keepalive: true,
  })
    .then((response) => {
      if (response.ok) {
        console.log('Shutdown request sent successfully');
      } else {
        console.error(
          `Shutdown request failed with status: ${response.status}`,
        );
      }
      shutdownInProgress = false; // Reset on success or handled failure
    })
    .catch((error) => {
      console.error('Shutdown request failed:', error);
      shutdownInProgress = false; // Reset on error
    });
};

export const stopServer = async () => {
  if (shutdownInProgress) {
    console.log('Shutdown already in progress, skipping...');
    return;
  }
  shutdownInProgress = true;

  try {
    if (!(await isServerRunning())) {
      shutdownInProgress = false;
      return;
    }

    const shutdownSuccessful = await attemptGracefulShutdown();

    if (shutdownSuccessful) {
      console.log('Server shutdown completed gracefully');
      shutdownInProgress = false;
      return;
    }

    await sleep(SHUTDOWN_RECHECK_DELAY_MS);

    if (!(await isServerRunning())) {
      shutdownInProgress = false;
      return;
    }

    console.warn('Graceful shutdown timed out, attempting force kill...');
    await forceKillServer();
    shutdownInProgress = false;
  } catch (error) {
    console.error('Error stopping server:', error);
    try {
      await forceKillServer();
    } catch (forceKillError) {
      console.error('Force kill also failed:', forceKillError);
    }
    shutdownInProgress = false;
  }
};

async function attemptGracefulShutdown(): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), SHUTDOWN_TIMEOUT_MS);

    const response = await fetch(`${BACKEND_URL}/shutdown`, {
      method: 'POST',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.ok) {
      // Consume response body (may be empty if 204 No Content)
      await response.text().catch(() => {});
      return true;
    } else {
      console.warn(response.status);
      return false;
    }
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.warn('Shutdown request timed out');
    } else {
      console.warn('Error during graceful shutdown:', error);
    }
    return false;
  }
}

async function forceKillServer(): Promise<void> {
  try {
    const platformName = isWindows() ? 'windows' : 'unix';
    console.log(`Force killing server on platform: ${platformName}`);

    const commandName = isWindows() ? 'killProcessWindows' : 'killProcessUnix';

    await Command.create(commandName, '').execute();
  } catch (error) {
    console.error('Error during force kill:', error);
    throw error;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export const restartServer = async () => {
  try {
    await stopServer();
    await sleep(2000);
    await startServer();
  } catch (error) {
    console.error('Error restarting server:', error);
    throw error;
  }
};
