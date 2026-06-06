import { spawn } from 'child_process';
import os from 'os';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const bashScript = path.join(__dirname, 'setup.sh');
const psScript = path.join(__dirname, 'setup.ps1');

let command, args;

if (os.platform() === 'win32') {
  // On Windows, use PowerShell
  command = 'powershell.exe';
  args = ['-ExecutionPolicy', 'Bypass', '-File', psScript];
} else if (os.platform() === 'linux') {
  // Check if it's Debian-based Linux
  const debianVersionPath = '/etc/debian_version';
  if (fs.existsSync(debianVersionPath)) {
    // On Debian-based Linux, use the bash script
    command = bashScript;
    args = [];

    // Ensure the bash script is executable; if not, set the execute permission.
    try {
      fs.accessSync(bashScript, fs.constants.X_OK);
    } catch (err) {
      console.log(`File ${bashScript} is not executable. Setting execute permission...`);
      fs.chmodSync(bashScript, 0o755);
    }
  } else {
    console.error('Unsupported Linux distribution. This setup script only supports Debian-based Linux distributions.');
    console.error('Please install system dependencies manually and run the individual setup commands.');
    process.exit(1);
  }
} else {
  console.error(`Unsupported operating system: ${os.platform()}`);
  console.error('This setup script only supports Windows and Debian-based Linux distributions.');
  console.error('Please install system dependencies manually and run the individual setup commands.');
  process.exit(1);
}

const proc = spawn(command, args, { stdio: 'inherit' });

proc.on('error', (err) => {
  console.error(`Failed to start setup: ${err}`);
});

proc.on('close', (code) => {
  console.log(`Setup finished with exit code ${code}`);
});
