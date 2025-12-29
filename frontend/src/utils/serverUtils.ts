import { Command } from '@tauri-apps/plugin-shell';
import { invoke } from '@tauri-apps/api/core';
import { BACKEND_URL } from '@/config/Backend.ts';

const SHUTDOWN_TIMEOUT_MS = 5000;
const SHUTDOWN_RECHECK_DELAY_MS = 1000;

const isWindows = (): boolean => {
  return navigator.userAgent.toLowerCase().includes('windows');
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
  console.log('Initialized backend shutdown...');

  fetch(`${BACKEND_URL}/shutdown`, {
    method: 'POST',
    keepalive: true,
  })
    .then(() => console.log('Shutdown request sent'))
    .catch((error) => console.error('Shutdown request failed:', error));
};

export const stopServer = async () => {
  try {
    if (!(await isServerRunning())) {
      return;
    }

    const shutdownSuccessful = await attemptGracefulShutdown();

    if (shutdownSuccessful) {
      console.log('Server shutdown completed gracefully');
      return;
    }

    await sleep(SHUTDOWN_RECHECK_DELAY_MS);

    if (!(await isServerRunning())) {
      return;
    }

    console.warn('Graceful shutdown timed out, attempting force kill...');
    await forceKillServer();
  } catch (error) {
    console.error('Error stopping server:', error);
    try {
      await forceKillServer();
    } catch (forceKillError) {
      console.error('Force kill also failed:', forceKillError);
    }
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
