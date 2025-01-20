import { Command } from '@tauri-apps/plugin-shell';
import { invoke } from '@tauri-apps/api/core';
export const serverInterface = () => {
  let setPid = (pid: string) => window.localStorage.setItem('pid', pid);
  let getPid = () => window.localStorage.getItem('pid');
  let startServer = async () => {
    let serverPath: string = await invoke('get_server_path');
    alert(serverPath);
    console.log(serverPath);
    const command = Command.create('StartServer', ['-c', './PictoPy_Server'], {
      cwd: serverPath,
    });
    command.on('close', (data) => {
      alert(data);
    });
    command.on('error', (error) => alert(error));
    command.stdout.on('data', (line) => alert(line));
    command.stderr.on('data', (line) => alert(line));
    const child = await command.spawn();
    alert(child);
    window.localStorage.setItem('pid', child.pid.toString());
    console.log('pid:', child.pid);
  };
  let restartServer = async (setIsLoading: (val: boolean) => void) => {
    let pid = getPid();
    setIsLoading(true);
    if (pid) {
      let result = await Command.create('killProcess', [
        '-c',
        `kill -SIGINT ${pid}`,
      ]).execute();
      console.log(result);
      alert(result);
      if (result.code === 0) {
        setPid('');
        setTimeout(async () => {
          await startServer();
          setIsLoading(false);
        }, 2000);
      } else {
        setPid('');
        throw new Error('Error restarting server');
      }
    } else {
      startServer();
    }
  };
  let stopServer = async () => {
    let pid = getPid();
    if (pid) {
      let result = await Command.create('killProcess', [
        '-c',
        `kill -SIGINT ${pid}`,
      ]).execute();
      console.log(result);
      if (result.code === 0) {
        setPid('');
      } else {
        setPid('');
        throw new Error('Error stopping server');
      }
    }
  };
  return { startServer, restartServer, stopServer };
};
