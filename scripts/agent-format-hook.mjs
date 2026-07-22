#!/usr/bin/env node
// Claude Code hook: auto-formats files an agent edits, and blocks `ruff format`.
// Registered in .claude/settings.json. Reads the hook payload as JSON on stdin.
//
// Two modes:
//   (no args)  PostToolUse on Edit|Write — format the edited file
//   --guard    PreToolUse on Bash — deny `ruff format`, which would reflow the
//              Python codebase to Ruff's 300-column width and fight black.

import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const GUARD = process.argv.includes('--guard');
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function readStdin() {
  try {
    // fd 0 blocks until the hook payload is written and stdin closes.
    return readFileSync(0, 'utf8');
  } catch {
    return '';
  }
}

/** Run a command, swallowing "not installed" so a partial dev env isn't blocked. */
function run(cmd, args, cwd) {
  const result = spawnSync(cmd, args, {
    cwd,
    shell: process.platform === 'win32',
    stdio: 'ignore',
  });
  return result.error === undefined && result.status === 0;
}

/**
 * True when `ruff format` is actually being executed, rather than merely mentioned
 * inside a quoted argument such as a commit message or an echo.
 */
function runsRuffFormat(command) {
  // Drop quoted strings first, so prose mentioning "ruff format" doesn't match.
  const unquoted = command
    .replace(/'[^']*'/g, "''")
    .replace(/"(?:[^"\\]|\\.)*"/g, '""');

  // Then require it at the start of a command segment, not buried in arguments.
  return unquoted
    .split(/&&|\|\||[;|\n]/)
    .some((segment) => /^\s*(?:\w+=\S+\s+)*ruff\s+format\b/.test(segment));
}

function guard(payload) {
  const command = payload?.tool_input?.command ?? '';
  if (runsRuffFormat(command)) {
    // exit 2 tells Claude Code to block the call and show stderr to the model.
    process.stderr.write(
      'Blocked: `ruff format` would reflow this codebase to 300 columns.\n' +
        'Python here is formatted with black at 88 columns. Use:\n' +
        '  pre-commit run --config .pre-commit-config.yaml --all-files\n',
    );
    process.exit(2);
  }
  process.exit(0);
}

function format(payload) {
  const filePath = payload?.tool_input?.file_path;
  if (!filePath || !existsSync(filePath)) process.exit(0);

  const ext = path.extname(filePath).toLowerCase();
  const rel = path.relative(REPO_ROOT, filePath);

  // Never reformat generated, vendored, or dependency trees.
  if (/(^|[\\/])(node_modules|dist|target|gen|__pycache__|site-packages)[\\/]/.test(rel)) {
    process.exit(0);
  }

  if (ext === '.py') {
    run('black', ['--quiet', filePath], REPO_ROOT);
  } else if (['.ts', '.tsx', '.js', '.jsx', '.json'].includes(ext)) {
    const frontend = path.join(REPO_ROOT, 'frontend');
    run('npx', ['--no-install', 'prettier', '--write', filePath], frontend);
    run('npx', ['--no-install', 'eslint', '--fix', filePath], frontend);
  } else if (ext === '.rs') {
    run('cargo', ['fmt', '--', filePath], path.join(REPO_ROOT, 'frontend', 'src-tauri'));
  }

  process.exit(0);
}

let payload = {};
try {
  payload = JSON.parse(readStdin() || '{}');
} catch {
  process.exit(0);
}

if (GUARD) guard(payload);
else format(payload);
