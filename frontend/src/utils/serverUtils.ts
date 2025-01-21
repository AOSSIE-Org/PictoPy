import { Command } from '@tauri-apps/plugin-shell';
import { invoke } from '@tauri-apps/api/core';
import { BACKED_URL } from '../Config/Backend.ts';

const isWindows = () => navigator.platform.startsWith('Win');

//Process ID of FastAPI Server:
const setPid = (pid: string) => window.localStorage.setItem('pid', pid);
const getPid = () => window.localStorage.getItem('pid') || '';

const getCommand = (action: 'start' | 'stop', pid?: string): string[] => {
  if (action === 'start') {
    return isWindows() ? ['./PictoPy_Server'] : ['-c', './PictoPy_Server'];
  }
  if (action === 'stop' && pid) {
    return isWindows() ? [`taskkill /t /f /im PictoPy_Server.exe`] : ['-c', `kill -SIGINT ${pid}`];
  }
  throw new Error('Invalid action or missing PID for stop command');
};


const isServerRunning = async (): Promise<boolean> => {
  try {
    const response = await fetch(BACKED_URL);
    if (response.ok) {
      console.log("Server is Running!")
      return true;
    } else {
      setPid('');
      return false;
    }
  } catch (error) {
    console.error('Error checking server status:', error);
    setPid('');
    return false;
  }
};

export const startServer = async () => {
  try {
    if (!(await isServerRunning())) {
      const serverPath: string = await invoke('get_server_path');
      const command = Command.create(
        isWindows() ? 'StartServerWindows' : 'StartServerUnix',
        getCommand('start'),
        { cwd: serverPath }
      );

      const child = await command.spawn();
      command.stderr.on('data', (line) => console.error('Error:', line));
      setPid(child.pid.toString());
      console.log('Server started with PID:', child.pid);
    }
  } catch (error) {
    console.error('Error starting server:', error);
  }
};

export const stopServer = async () => {
  try {
    console.log("HIIII!");
    if(await isServerRunning())
    {
      const pid:string = getPid();
      console.log(pid);
        const result = await Command.create(
          isWindows() ? 'killProcessWindows' : 'killProcessUnix',
          getCommand('stop', pid)
        ).execute();
        console.log(result);
        setPid('');
    }
  } catch (error) {
    setPid('');
    console.error('Error stopping server:', error);
  }
};

export const restartServer = async (setIsLoading: (val: boolean) => void) => {
  try {
    setIsLoading(true);
    await stopServer();
    await startServer();
    setIsLoading(false);
  } catch (error) {
    setIsLoading(false);
    console.error('Error restarting server:', error);
    throw error;
  }
};
