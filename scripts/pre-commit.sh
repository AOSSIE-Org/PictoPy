#!/bin/sh
. "$(dirname "$0")/../.husky/_/husky.sh"

echo "Running lint-staged for React..."
npx lint-staged || exit 1

echo "Running Python linters..."
pre-commit run --config .pre-commit-config.yaml --all-files || exit 1

echo "Checking Rust code formatting..."
(cd frontend/src/src-tauri && cargo fmt -- --check && cargo clippy -- -D warnings )|| exit 1

echo "All linting checks passed."