#!/usr/bin/env node
// Regression tests for the agent format hook.
//
// Run: node scripts/agent-format-hook.test.mjs
// Also runs in CI, in the Linting job of .github/workflows/pr-check-tests.yml.
//
// Two layers: the guard and exclusion helpers directly, then the real entrypoint
// as a subprocess, because Claude Code depends on its exit codes (2 blocks, 0 allows).

import { spawnSync } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { runsRuffFormat, isExcluded, repoRelative } from './agent-format-hook.mjs';

const HOOK = path.join(path.dirname(fileURLToPath(import.meta.url)), 'agent-format-hook.mjs');
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

let ran = 0;
let failed = 0;
const skipped = [];
function check(ok, label) {
  ran++;
  if (!ok) {
    failed++;
    console.error(`FAIL  ${label}`);
  }
}

// ------------------------------------------------------- guard detection

// [command, should be blocked]
const GUARD_CASES = [
  // Direct invocations.
  ['ruff format backend/', true],
  ['ruff format .', true],
  ['ruff format --help', true],
  ['cd backend && ruff format .', true],
  ['pre-commit run; ruff format', true],
  ['echo ok & ruff format', true],
  ['ruff format . | tee log.txt', true],
  ['RUFF_CACHE_DIR=/tmp ruff format .', true],

  // Wrapped in a shell.
  ["bash -c 'ruff format src/x.py'", true],
  ['sh -c "ruff format ."', true],
  ['bash -c "cd backend && ruff format ."', true],

  // Launched through a runner.
  ['uv run ruff format', true],
  ['poetry run ruff format .', true],
  ['python -m ruff format .', true],
  ['python3.11 -m ruff format .', true],

  // Must NOT block: a different Ruff subcommand.
  ['ruff check --fix backend/', false],
  ['ruff check .', false],

  // Must NOT block: merely mentioned inside a quoted argument.
  ['git commit -m "chore: block `ruff format` in hooks"', false],
  ["git commit -m 'note: ruff format is banned'", false],
  ['git commit -m "fix; ruff format now blocked"', false],
  ['echo "do not run ruff format"', false],

  // Must NOT block: unrelated commands.
  ['npm test', false],
  ['black backend/', false],
  ['', false],
];

for (const [command, expected] of GUARD_CASES) {
  check(runsRuffFormat(command) === expected, `guard ${JSON.stringify(command)}`);
}

// ------------------------------------------------------- path exclusion

// [relative path, should be skipped by the formatter]
const EXCLUSION_CASES = [
  ['frontend/package-lock.json', true],
  ['package-lock.json', true],
  ['frontend/src/components/ui/button.tsx', true],
  ['frontend/node_modules/pkg/index.ts', true],
  ['backend/__pycache__/x.py', true],
  ['backend/.ruff_cache/x.py', true],
  ['backend/htmlcov/index.json', true],
  ['frontend/src-tauri/target/debug/x.rs', true],
  ['../outside-the-repo.py', true],

  ['backend/app/routes/videos.py', false],
  ['frontend/src/features/videoSlice.ts', false],
  ['frontend/src/components/Media/Player.tsx', false],
];

for (const [rel, expected] of EXCLUSION_CASES) {
  const native = rel.split('/').join(path.sep);
  check(isExcluded(native) === expected, `exclude ${rel}`);
}

// ------------------------------------------------- entrypoint (subprocess)

function runHook(args, payload) {
  return spawnSync(process.execPath, [HOOK, ...args], {
    input: typeof payload === 'string' ? payload : JSON.stringify(payload),
    encoding: 'utf8',
  });
}

// Guard mode: blocked invocations exit 2 and explain why on stderr.
{
  const r = runHook(['--guard'], { tool_input: { command: 'ruff format backend/' } });
  check(r.status === 2, 'entrypoint: blocked command exits 2');
  check(/Blocked/.test(r.stderr), 'entrypoint: blocked command explains itself on stderr');
  check(/black/.test(r.stderr), 'entrypoint: blocked command names the correct formatter');
}

// Guard mode: allowed invocations exit 0 silently.
{
  const r = runHook(['--guard'], { tool_input: { command: 'ruff check --fix .' } });
  check(r.status === 0, 'entrypoint: allowed command exits 0');
  check(r.stderr === '', 'entrypoint: allowed command is silent');
}

// Guard mode: fail open rather than blocking the session on bad input.
for (const [label, payload] of [
  ['malformed JSON', 'not json at all'],
  ['empty stdin', ''],
  ['missing tool_input', {}],
]) {
  const r = runHook(['--guard'], payload);
  check(r.status === 0, `entrypoint: ${label} exits 0`);
}

// Format mode: a missing file is a no-op, not a crash.
{
  const r = runHook([], { tool_input: { file_path: path.join(REPO_ROOT, 'does-not-exist.py') } });
  check(r.status === 0, 'entrypoint: missing file exits 0');
}

// Format mode: an excluded path is left byte-for-byte alone.
// The probe lives in its own mkdtemp directory so a manual run can never clobber
// a real file in the shadcn-generated tree.
{
  const uiDir = path.join(REPO_ROOT, 'frontend', 'src', 'components', 'ui');
  const probeDir = mkdtempSync(path.join(uiDir, '__hook_probe__-'));
  const probe = path.join(probeDir, 'probe.json');
  const ugly = '{"b":2,   "a":1}\n';
  writeFileSync(probe, ugly);
  try {
    const r = runHook([], { tool_input: { file_path: probe } });
    check(r.status === 0, 'entrypoint: excluded path exits 0');
    check(readFileSync(probe, 'utf8') === ugly, 'entrypoint: excluded path is not rewritten');
  } finally {
    rmSync(probeDir, { recursive: true, force: true });
  }
}

// Format mode: a path outside the repository is refused.
{
  const dir = mkdtempSync(path.join(tmpdir(), 'hook-test-'));
  const outside = path.join(dir, 'scratch.py');
  const ugly = 'def  f( a,b ):\n    return a\n';
  writeFileSync(outside, ugly);
  try {
    const r = runHook([], { tool_input: { file_path: outside } });
    check(r.status === 0, 'entrypoint: outside-repo path exits 0');
    check(readFileSync(outside, 'utf8') === ugly, 'entrypoint: outside-repo path is not rewritten');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

// Format mode: an in-repository symlink pointing outside the repository is refused.
// A lexical path check would see an in-repository path here and format the target.
{
  const outsideDir = mkdtempSync(path.join(tmpdir(), 'hook-test-link-'));
  const target = path.join(outsideDir, 'target.py');
  const linkDir = mkdtempSync(path.join(REPO_ROOT, 'backend', '__hook_probe__-'));
  const link = path.join(linkDir, 'link.py');
  const ugly = 'def  f( a,b ):\n    return a\n';
  writeFileSync(target, ugly);

  let linkViaJunction = null;
  let linked = true;
  try {
    symlinkSync(target, link, 'file');
  } catch {
    // Windows blocks file symlinks without Developer Mode, but permits directory
    // junctions. A junction reproduces the same escape, so fall back to one.
    try {
      symlinkSync(outsideDir, path.join(linkDir, 'dir'), 'junction');
      linkViaJunction = path.join(linkDir, 'dir', 'target.py');
    } catch {
      linked = false;
    }
  }

  try {
    if (linked) {
      const escaping = linkViaJunction ?? link;
      const r = runHook([], { tool_input: { file_path: escaping } });
      check(r.status === 0, 'entrypoint: escaping link exits 0');
      check(
        readFileSync(target, 'utf8') === ugly,
        'entrypoint: escaping link target is not rewritten',
      );
      // The lexical path looks in-repository; only link resolution catches it.
      const rel = repoRelative(escaping);
      check(rel === null || isExcluded(rel), 'boundary: escaping link is refused');
      check(
        !isExcluded(path.relative(REPO_ROOT, escaping)),
        'boundary: a lexical check would have let it through',
      );
    } else {
      skipped.push('escaping link (no permission to create a symlink or junction)');
      const rel = repoRelative(target);
      check(rel === null || isExcluded(rel), 'boundary: outside-repo target is refused');
      check(repoRelative(path.join(REPO_ROOT, 'backend')) === 'backend', 'boundary: in-repo path resolves');
    }
  } finally {
    rmSync(linkDir, { recursive: true, force: true });
    rmSync(outsideDir, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------- report

for (const note of skipped) {
  console.log(`SKIP  ${note} — asserted the boundary logic directly instead`);
}
if (failed === 0) {
  console.log(`All ${ran} checks passed.`);
} else {
  console.error(`\n${failed} of ${ran} checks failed.`);
  process.exit(1);
}
