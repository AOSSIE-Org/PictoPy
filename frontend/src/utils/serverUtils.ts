import { Command } from '@tauri-apps/plugin-shell';
import { invoke } from '@tauri-apps/api/core';
import { BACKEND_URL, SYNC_MICROSERVICE_URL } from '@/config/Backend.ts';
const isWindows = () => navigator.platform.startsWith('Win');

const isServerRunning = async (): Promise<boolean> => {
  try {
    const response = await fetch(BACKEND_URL + '/health');
    if (response.ok) {
      console.log('Server is Running!');
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
