#!/usr/bin/env node
// Claude Code hook: auto-formats files an agent edits, and blocks the Ruff formatter.
// Registered in .claude/settings.json. Reads the hook payload as JSON on stdin.
//
// Two modes:
//   (no args)  PostToolUse on Edit|Write — format the edited file
//   --guard    PreToolUse on Bash — deny `ruff format`, which would reflow the
//              Python codebase to Ruff's 300-column width and fight black.
//
// Regression tests: node scripts/agent-format-hook.test.mjs

import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, realpathSync } from 'node:fs';
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

/**
 * Run a formatter. Never uses a shell: the file path comes from the hook payload,
 * and on Windows `shell: true` would hand it to cmd.exe where a filename
 * containing shell metacharacters could execute arbitrary commands.
 * A missing toolchain is not an error — a frontend-only contributor has no black.
 */
function run(cmd, args, cwd) {
  const result = spawnSync(cmd, args, { cwd, shell: false, stdio: 'ignore' });
  return result.error === undefined && result.status === 0;
}

/** Node entry points, so prettier/eslint run without a .cmd shim (which would need a shell). */
function nodeBin(pkg, entry) {
  const p = path.join(REPO_ROOT, 'frontend', 'node_modules', pkg, entry);
  return existsSync(p) ? p : null;
}

// ---------------------------------------------------------------- guard mode

const RUNNER_PREFIX = /^(?:uv|poetry|pipx|pdm|hatch|rye)\s+run\s+/;
const PYTHON_M_PREFIX = /^python[0-9.]*\s+-m\s+/;
const ENV_PREFIX = /^(?:\w+=\S*\s+)+/;

/** True when a single command segment invokes the Ruff formatter. */
function isRuffFormatCommand(segment) {
  let s = segment.trim().replace(ENV_PREFIX, '');

  // Peel runner wrappers: `uv run ruff format`, `python -m ruff format`.
  for (;;) {
    const next = s.replace(RUNNER_PREFIX, '').replace(PYTHON_M_PREFIX, '');
    if (next === s) break;
    s = next;
  }

  return /^ruff\s+format\b/.test(s);
}

/**
 * True when `ruff format` is actually executed, rather than merely mentioned
 * inside a quoted argument such as a commit message or an echo.
 */
function runsRuffFormat(command, depth = 0) {
  if (depth > 3) return false;

  // Recurse into `sh -c "<payload>"` so wrapped invocations are still caught.
  // Only a shell's -c flag unwraps a quoted string; `git commit -m "..."` does not.
  const wrapped =
    /\b(?:sh|bash|zsh|dash|ksh|pwsh|powershell(?:\.exe)?|cmd(?:\.exe)?)\s+(?:-c|-Command|\/[cC])\s+(?:'([^']*)'|"((?:[^"\\]|\\.)*)")/g;
  for (const match of command.matchAll(wrapped)) {
    if (runsRuffFormat(match[1] ?? match[2] ?? '', depth + 1)) return true;
  }

  // Blank quoted strings so prose mentioning the command doesn't trigger a block.
  const unquoted = command
    .replace(/'[^']*'/g, "''")
    .replace(/"(?:[^"\\]|\\.)*"/g, '""');

  // Split on command separators, including a single `&` for background jobs.
  return unquoted.split(/&&|\|\||[;|&\n]/).some(isRuffFormatCommand);
}

function guard(payload) {
  if (runsRuffFormat(payload?.tool_input?.command ?? '')) {
    // exit 2 tells Claude Code to block the call and show stderr to the model.
    process.stderr.write(
      'Blocked: the Ruff formatter would reflow this codebase to 300 columns.\n' +
        'Python here is formatted with black at 88 columns. Use:\n' +
        '  pre-commit run --config .pre-commit-config.yaml --all-files\n',
    );
    process.exit(2);
  }
  process.exit(0);
}

// --------------------------------------------------------------- format mode

// Generated, vendored, or cache trees that must never be reformatted.
const EXCLUDED_DIRS =
  /(^|[\\/])(node_modules|dist|target|gen|__pycache__|site-packages|\.mypy_cache|\.ruff_cache|htmlcov)[\\/]/;

// Specific protected paths, matched against a forward-slash relative path.
const EXCLUDED_PATHS = [
  'frontend/src/components/ui/', // shadcn-generated
];
const EXCLUDED_FILES = ['frontend/package-lock.json', 'package-lock.json'];

function isExcluded(rel) {
  const normalized = rel.split(path.sep).join('/');
  // Outside the repository. On Windows, path.relative across drives returns an
  // absolute path rather than a '..' prefix, so both forms have to be checked.
  if (normalized.startsWith('..') || path.isAbsolute(rel)) return true;
  if (EXCLUDED_DIRS.test(rel)) return true;
  if (EXCLUDED_FILES.includes(normalized)) return true;
  return EXCLUDED_PATHS.some((prefix) => normalized.startsWith(prefix));
}

/**
 * Repository-relative path for a file, with symlinks resolved on both sides.
 * A lexical path.relative() would accept an in-repository symlink whose target
 * lives outside the repository, and the formatter would then rewrite that target.
 * Returns null when the path cannot be resolved.
 */
function repoRelative(filePath) {
  try {
    return path.relative(realpathSync(REPO_ROOT), realpathSync(filePath));
  } catch {
    return null;
  }
}

function format(payload) {
  const filePath = payload?.tool_input?.file_path;
  if (!filePath || !existsSync(filePath)) process.exit(0);

  const rel = repoRelative(filePath);
  if (rel === null || isExcluded(rel)) process.exit(0);

  const ext = path.extname(filePath).toLowerCase();

  if (ext === '.py') {
    run('black', ['--quiet', filePath], REPO_ROOT);
  } else if (['.ts', '.tsx', '.js', '.jsx', '.json'].includes(ext)) {
    const frontend = path.join(REPO_ROOT, 'frontend');
    const prettier = nodeBin('prettier', path.join('bin', 'prettier.cjs'));
    const eslint = nodeBin('eslint', path.join('bin', 'eslint.js'));
    if (prettier) run(process.execPath, [prettier, '--write', filePath], frontend);
    if (eslint) run(process.execPath, [eslint, '--fix', filePath], frontend);
  } else if (ext === '.rs') {
    run('cargo', ['fmt', '--', filePath], path.join(REPO_ROOT, 'frontend', 'src-tauri'));
  }

  process.exit(0);
}

// ---------------------------------------------------------------------- main

export { runsRuffFormat, isExcluded, repoRelative };

// Only act when run as the hook, so the test file can import the helpers above.
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  let payload = {};
  try {
    payload = JSON.parse(readStdin() || '{}');
  } catch {
    process.exit(0);
  }
  if (GUARD) guard(payload);
  else format(payload);
}
