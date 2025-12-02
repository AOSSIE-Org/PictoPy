#!/usr/bin/env node
const { spawnSync, spawn } = require('child_process');

function hasTauriCli() {
  try {
    const res = spawnSync('tauri', ['--version'], { stdio: 'ignore' });
    return res.status === 0;
  } catch (e) {
    return false;
  }
}

if (hasTauriCli()) {
  console.log('Tauri CLI detected. Running `tauri dev`...');
  const child = spawn('tauri', ['dev'], { stdio: 'inherit', shell: true });
  child.on('exit', (code) => process.exit(code));
} else {
  console.warn('Tauri CLI not found locally. Falling back to starting the web dev server (vite).');
  console.warn('If you want full Tauri dev experience, install Tauri toolchain (Rust + @tauri-apps/cli).');
  const child = spawn('npm', ['run', 'dev'], { stdio: 'inherit', shell: true });
  child.on('exit', (code) => process.exit(code));
}
