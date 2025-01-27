import { Command } from '@tauri-apps/plugin-shell';
import { invoke } from '@tauri-apps/api/core';
import { BACKED_URL } from '../Config/Backend.ts';
const isWindows = () => navigator.platform.startsWith('Win');

const isServerRunning = async (): Promise<boolean> => {
  try {
    const response = await fetch(BACKED_URL);
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

export const startServer = async () => {
  try {
    console.log('Starting!');
    if (!(await isServerRunning())) {
      const serverPath: string = await invoke('get_server_path');
      const command = Command.create(
        isWindows() ? 'StartServerWindows' : 'StartServerUnix',
        '',
        { cwd: serverPath },
      );

      const child = await command.spawn();
      command.stderr.on('data', (line) => console.error('Error:', line));
      console.log('Server started with PID:', child.pid);
    }
  } catch (error) {
    console.error('Error starting server:', error);
  }
};

export const stopServer = async () => {
  try {
    console.log('Stopping!');
    if (await isServerRunning()) {
      const result = await Command.create(
        isWindows() ? 'killProcessWindows' : 'killProcessUnix',
        '',
      ).execute();
      console.log(result);
    }
  } catch (error) {
    console.error('Error stopping server:', error);
  }
};

export const restartServer = async (setIsLoading: (val: boolean) => void) => {
  try {
    setIsLoading(true);
    await stopServer();
    setTimeout(async () => {
      await startServer();
      setIsLoading(false);
    }, 2000);
  } catch (error) {
    setIsLoading(false);
    console.error('Error restarting server:', error);
    throw error;
  }
};
