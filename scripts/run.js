// Unified dev/prod launcher for PictoPy: backend, sync-microservice, and frontend.
// Node.js port of run.sh with identical behavior, for native Windows (cmd/PowerShell)
// support without requiring Git Bash or WSL.
//
// On Linux, macOS, Git Bash, or WSL you can also use `bash scripts/run.sh`.
//
// Usage:
//   node scripts/run.js          -> dev mode (default)
//   node scripts/run.js --prod   -> production mode

import { spawn, spawnSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// --- Colors (matches scripts/run.sh / scripts/setup.sh conventions) ---
const RED = '\x1b[0;31m';
const GREEN = '\x1b[0;32m';
const YELLOW = '\x1b[0;33m';
const NC = '\x1b[0m';

const MODE = process.argv[2] === '--prod' ? 'prod' : 'dev';

const ROOT_DIR = path.resolve(__dirname, '..');
const BACKEND_DIR = path.join(ROOT_DIR, 'backend');
const SYNC_DIR = path.join(ROOT_DIR, 'sync-microservice');
const FRONTEND_DIR = path.join(ROOT_DIR, 'frontend');

// --- OS detection (same approach as scripts/run.sh and scripts/setup.js) ---
let OS_TYPE;
switch (process.platform) {
  case 'linux':
    OS_TYPE = 'linux';
    break;
  case 'darwin':
    OS_TYPE = 'macos';
    break;
  case 'win32':
    OS_TYPE = 'windows';
    break;
  default:
    OS_TYPE = 'unknown';
    console.log(`${YELLOW}Warning: unrecognized platform '${process.platform}'. Assuming Unix-like behavior.${NC}`);
}
const IS_WINDOWS = OS_TYPE === 'windows';

const SETUP_HINT = IS_WINDOWS
  ? "Run 'npm run setup' from the repo root (this launches scripts/setup.ps1 on Windows)."
  : "Run 'npm run setup' from the repo root to install dependencies.";

// --- Preflight: fail fast with guidance instead of a raw "command not found" ---
function commandExists(cmd) {
  const pathEnv = process.env.PATH || process.env.Path || '';
  const dirs = pathEnv.split(path.delimiter).filter(Boolean);
  const exts = IS_WINDOWS ? (process.env.PATHEXT || '.EXE;.CMD;.BAT;.COM').split(';') : [''];
  for (const dir of dirs) {
    for (const ext of exts) {
      const candidate = path.join(dir, cmd + ext);
      try {
        fs.accessSync(candidate, fs.constants.X_OK);
        return candidate;
      } catch {
        // keep searching
      }
    }
  }
  return null;
}

function requireCmd(cmd, guidance) {
  if (!commandExists(cmd)) {
    console.error(`${RED}Error: required command '${cmd}' not found.${NC}`);
    console.error(`${YELLOW}${guidance}${NC}`);
    process.exit(1);
  }
}

function requireDir(dir, label) {
  if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) {
    console.error(`${RED}Error: ${label} directory not found at ${dir}${NC}`);
    console.error(`${YELLOW}Make sure you're running this from a full PictoPy checkout.${NC}`);
    process.exit(1);
  }
}

requireDir(BACKEND_DIR, 'backend');
requireDir(SYNC_DIR, 'sync-microservice');
requireDir(FRONTEND_DIR, 'frontend');

requireCmd('node', `Node.js not found. Install it from https://nodejs.org, or ${SETUP_HINT}`);
requireCmd('npm', `npm not found (usually bundled with Node.js). Install Node.js from https://nodejs.org, or ${SETUP_HINT}`);
requireCmd('cargo', `Rust/Cargo not found (required by 'npm run tauri dev'). Install it from https://rustup.rs, or ${SETUP_HINT}`);

// --- venv resolution helper ---
// Tries each candidate venv folder name in order, using the correct
// bin dir per OS (bin/ on Unix, Scripts/ on Windows). Instead of "sourcing"
// activate (there's no such thing for a child process spawned from Node),
// the resolved bin dir is prepended to PATH for that child.
function resolveVenv(baseDir, candidates) {
  for (const name of candidates) {
    const venvDir = path.join(baseDir, name);
    const binDir = path.join(venvDir, IS_WINDOWS ? 'Scripts' : 'bin');
    if (fs.existsSync(path.join(binDir, 'activate'))) {
      return { venvDir, binDir };
    }
  }
  console.error(`${RED}Could not find a venv in ${baseDir} (looked for: ${candidates.join(', ')})${NC}`);
  console.error(`${YELLOW}${SETUP_HINT}${NC}`);
  return null;
}

// --- process orchestration ---
const children = [];
let aliveCount = 0;
let shuttingDown = false;

function prefixStream(stream, prefix, out) {
  let buffer = '';
  stream.setEncoding('utf8');
  stream.on('data', (chunk) => {
    buffer += chunk;
    const lines = buffer.split('\n');
    buffer = lines.pop();
    for (const line of lines) {
      out.write(`[${prefix}] ${line}\n`);
    }
  });
  stream.on('end', () => {
    if (buffer.length > 0) {
      out.write(`[${prefix}] ${buffer}\n`);
      buffer = '';
    }
  });
}

function spawnService(prefix, command, args, options) {
  const child = spawn(command, args, {
    stdio: ['ignore', 'pipe', 'pipe'],
    ...options,
  });

  prefixStream(child.stdout, prefix, process.stdout);
  prefixStream(child.stderr, prefix, process.stdout); // merged like run.sh's 2>&1

  child.on('error', (err) => {
    process.stdout.write(`[${prefix}] Failed to start: ${err.message}\n`);
  });

  aliveCount++;
  child.on('exit', () => {
    aliveCount--;
    if (aliveCount === 0 && !shuttingDown) {
      process.exit(0);
    }
  });

  children.push(child);
  return child;
}

function killChild(child) {
  if (!child.pid || child.exitCode !== null || child.signalCode !== null) return;
  if (IS_WINDOWS) {
    spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F']);
  } else {
    try {
      process.kill(-child.pid, 'SIGTERM');
    } catch {
      try {
        child.kill('SIGTERM');
      } catch {
        // process already gone
      }
    }
  }
}

function cleanup() {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log('');
  console.log('Shutting down all services...');
  for (const child of children) {
    killChild(child);
  }
  process.exit(0);
}
process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

function venvEnv(binDir) {
  return {
    ...process.env,
    PATH: `${binDir}${path.delimiter}${process.env.PATH || process.env.Path || ''}`,
    // Node pipes child stdio, so Python sees a non-tty and fully buffers
    // stdout instead of line-buffering it. Force unbuffered output so
    // uvicorn/fastapi logs show up live instead of only on exit.
    PYTHONUNBUFFERED: '1',
    // Without a real console attached, rich (used by `fastapi dev`'s banner)
    // falls back to the legacy Windows console writer, which encodes with
    // cp1252 and crashes on the emoji in its own startup banner. Forcing
    // UTF-8 mode avoids that.
    PYTHONUTF8: '1',
  };
}

// pip/uvicorn/fastapi console-script .exe launchers generated inside a venv
// have turned out to be unreliable on this Windows setup (some fail
// instantly with no output, e.g. "Fatal error in launcher: Unable to find
// an appended archive"). Invoking everything as `python -m <module>`
// sidesteps those launcher stubs entirely and has proven reliable.
function venvPython(venv) {
  const python = path.join(venv.binDir, IS_WINDOWS ? 'python.exe' : 'python');
  if (!fs.existsSync(python)) {
    console.error(`${RED}'python' not found in venv at ${venv.venvDir}.${NC}`);
    process.exit(1);
  }
  return python;
}

// Installs a service's Python dependencies before starting it, matching
// `source <venv>/activate && pip install -r requirements.txt` from the
// project's README. Blocking by design: the server must not start against
// a venv with missing/outdated packages.
function pipInstall(prefix, serviceDir, venv, python) {
  console.log(`[${prefix}] Installing dependencies from requirements.txt...`);
  const result = spawnSync(python, ['-m', 'pip', 'install', '-r', 'requirements.txt'], {
    cwd: serviceDir,
    env: venvEnv(venv.binDir),
    stdio: 'inherit',
  });
  if (result.status !== 0) {
    console.error(`${RED}[${prefix}] pip install -r requirements.txt failed.${NC}`);
    process.exit(1);
  }
}

function startBackend() {
  console.log(`[BACKEND] Starting... ${BACKEND_DIR}`);
  const venv = resolveVenv(BACKEND_DIR, ['.env', 'venv']);
  if (!venv) process.exit(1);
  const python = venvPython(venv);
  pipInstall('BACKEND', BACKEND_DIR, venv, python);

  const env = venvEnv(venv.binDir);
  if (MODE === 'prod') {
    console.log('[BACKEND] Starting in production mode on port 52123...');
    spawnService('BACKEND', python, ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '52123', '--workers', process.env.WORKERS || '1'], {
      cwd: BACKEND_DIR,
      env,
      detached: !IS_WINDOWS,
    });
  } else {
    // Backend pins fastapi-cli==0.0.3, which predates `fastapi.__main__`
    // (no `python -m fastapi` support), unlike sync-microservice's newer
    // fastapi-cli. Use uvicorn directly here instead.
    console.log('[BACKEND] Starting in dev mode on port 52123...');
    spawnService('BACKEND', python, ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '52123', '--reload'], {
      cwd: BACKEND_DIR,
      env,
      detached: !IS_WINDOWS,
    });
  }
}

function startSync() {
  const venv = resolveVenv(SYNC_DIR, ['.sync-env', 'venv']);
  if (!venv) process.exit(1);
  const python = venvPython(venv);
  pipInstall('SYNC', SYNC_DIR, venv, python);
  console.log('[SYNC] Starting sync-microservice on port 52124...');

  const env = venvEnv(venv.binDir);
  if (MODE === 'prod') {
    spawnService('SYNC', python, ['-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '52124'], {
      cwd: SYNC_DIR,
      env,
      detached: !IS_WINDOWS,
    });
  } else {
    spawnService('SYNC', python, ['-m', 'fastapi', 'dev', '--port', '52124'], {
      cwd: SYNC_DIR,
      env,
      detached: !IS_WINDOWS,
    });
  }
}

function startFrontend() {
  const nodeModules = path.join(FRONTEND_DIR, 'node_modules');
  if (!fs.existsSync(nodeModules)) {
    console.error(`${RED}[FRONTEND] node_modules not found.${NC}`);
    console.error(`${YELLOW}[FRONTEND] ${SETUP_HINT}${NC}`);
    process.exit(1);
  }
  console.log('[FRONTEND] Starting Tauri dev...');
  spawnService('FRONTEND', 'npm', ['run', 'tauri', 'dev'], {
    cwd: FRONTEND_DIR,
    env: process.env,
    shell: IS_WINDOWS, // npm ships as npm.cmd on Windows, which needs shell resolution
    detached: !IS_WINDOWS,
  });
}

console.log(`Starting PictoPy (mode: ${MODE}, OS: ${OS_TYPE})...`);
startBackend();
startSync();
startFrontend();
