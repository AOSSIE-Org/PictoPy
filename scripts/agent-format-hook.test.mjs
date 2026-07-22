#!/usr/bin/env node
// Regression tests for the agent format hook. Run: node scripts/agent-format-hook.test.mjs
//
// Not wired into CI — CI has no Node test job for scripts/. Run it by hand when
// changing the guard, and see agent-kit/references/ci-gates.md.

import { runsRuffFormat, isExcluded } from './agent-format-hook.mjs';

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

  // Must NOT block: different Ruff subcommand.
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

let failed = 0;

for (const [command, expected] of GUARD_CASES) {
  const actual = runsRuffFormat(command);
  if (actual !== expected) {
    failed++;
    console.error(`FAIL guard    got=${actual} want=${expected}  ${JSON.stringify(command)}`);
  }
}

for (const [rel, expected] of EXCLUSION_CASES) {
  const actual = isExcluded(rel.split('/').join(process.platform === 'win32' ? '\\' : '/'));
  if (actual !== expected) {
    failed++;
    console.error(`FAIL exclude  got=${actual} want=${expected}  ${rel}`);
  }
}

const total = GUARD_CASES.length + EXCLUSION_CASES.length;
if (failed === 0) {
  console.log(`All ${total} cases passed.`);
} else {
  console.error(`\n${failed} of ${total} cases failed.`);
  process.exit(1);
}
