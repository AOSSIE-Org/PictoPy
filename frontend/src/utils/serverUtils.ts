import { Command } from '@tauri-apps/plugin-shell';
import { invoke } from '@tauri-apps/api/core';
import { BACKEND_URL, SYNC_MICROSERVICE_URL } from '@/config/Backend.ts';

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
    const response = await fetch(BACKEND_URL + '/health');
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

const isSyncServiceRunning = async (): Promise<boolean> => {
  try {
    const response = await fetch(SYNC_MICROSERVICE_URL + '/health');
    if (response.ok) {
      console.log('Sync Service is Running!');
      return true;
    } else {
      return false;
    }
  } catch (error) {
    console.error('Error checking sync service status:', error);
    return false;
  }
};

export const startServer = async () => {
  try {
    // Wait for Tauri to be fully ready (fixes initialization race)
    const tauriReady = await waitForTauriReady();
    if (!tauriReady) {
      console.error('Tauri not ready, cannot start server');
      return;
    }

    console.log('Starting services!');

    const resourcesFolderPath: string = await invoke(
      'get_resources_folder_path',
    );

    // Start backend server
    if (!(await isServerRunning())) {
      const backendCommand = Command.create(
        isWindows() ? 'StartBackendWindows' : 'StartBackendUnix',
        '',
        { cwd: resourcesFolderPath + '/backend' },
      );

      const backendChild = await backendCommand.spawn();
      backendCommand.stderr.on('data', (line) =>
        console.error('Backend Error:', line),
      );
      console.log('Backend server started with PID:', backendChild.pid);
    }

    // Start sync service
    if (!(await isSyncServiceRunning())) {
      const syncCommand = Command.create(
        isWindows() ? 'StartSyncServiceWindows' : 'StartSyncServiceUnix',
        '',
        { cwd: resourcesFolderPath + '/sync-microservice' },
      );

      const syncChild = await syncCommand.spawn();
      syncCommand.stderr.on('data', (line) =>
        console.error('Sync Service Error:', line),
      );
      console.log('Sync service started with PID:', syncChild.pid);
    }
  } catch (error) {
    console.error('Error starting services:', error);
  }
};

// Fire-and-forget shutdown trigger for both services
export const triggerShutdown = (): void => {
  if (shutdownInProgress) {
    console.log('Shutdown already in progress, skipping...');
    return;
  }
  shutdownInProgress = true;
  console.log('Initialized shutdown for all services...');

  // Belt-and-suspenders: Always call forceKillServer to kill both Server and Sync
  forceKillServer().catch((err) =>
    console.error('Force kill during shutdown:', err),
  );

  // Send shutdown request to backend
  fetch(`${BACKEND_URL}/shutdown`, {
    method: 'POST',
    keepalive: true,
  })
    .then((response) => {
      if (response.ok) {
        console.log('Backend shutdown request sent successfully');
      } else {
        console.error(
          `Backend shutdown request failed with status: ${response.status}`,
        );
      }
    })
    .catch((error) => {
      console.error('Backend shutdown request failed:', error);
    });

  // Send shutdown request to sync service
  fetch(`${SYNC_MICROSERVICE_URL}/shutdown`, {
    method: 'POST',
    keepalive: true,
  })
    .then((response) => {
      if (response.ok) {
        console.log('Sync service shutdown request sent successfully');
      } else {
        console.error(
          `Sync service shutdown request failed with status: ${response.status}`,
        );
      }
    })
    .catch((error) => {
      console.error('Sync service shutdown request failed:', error);
    });

  // Reset flag after a delay
  setTimeout(() => {
    shutdownInProgress = false;
  }, 2000);
};

export const stopServer = async () => {
  if (shutdownInProgress) {
    console.log('Shutdown already in progress, skipping...');
    return;
  }
  shutdownInProgress = true;

  try {
    if (!(await isServerRunning()) && !(await isSyncServiceRunning())) {
      shutdownInProgress = false;
      return;
    }

    const shutdownSuccessful = await attemptGracefulShutdown();

    if (shutdownSuccessful) {
      console.log('Services shutdown completed gracefully');
      shutdownInProgress = false;
      return;
    }

    await sleep(SHUTDOWN_RECHECK_DELAY_MS);

    if (!(await isServerRunning()) && !(await isSyncServiceRunning())) {
      shutdownInProgress = false;
      return;
    }

    console.warn('Graceful shutdown timed out, attempting force kill...');
    await forceKillServer();
    shutdownInProgress = false;
  } catch (error) {
    console.error('Error stopping services:', error);
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

    // Try to shutdown both services
    const [backendResponse, syncResponse] = await Promise.allSettled([
      fetch(`${BACKEND_URL}/shutdown`, {
        method: 'POST',
        signal: controller.signal,
      }),
      fetch(`${SYNC_MICROSERVICE_URL}/shutdown`, {
        method: 'POST',
        signal: controller.signal,
      }),
    ]);

    clearTimeout(timeoutId);

    const backendOk =
      backendResponse.status === 'fulfilled' && backendResponse.value.ok;
    const syncOk = syncResponse.status === 'fulfilled' && syncResponse.value.ok;

    if (backendOk || syncOk) {
      return true;
    } else {
      console.warn('Shutdown requests did not succeed');
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
    console.log(`Force killing services on platform: ${platformName}`);

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
