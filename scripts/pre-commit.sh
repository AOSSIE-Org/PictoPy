#!/bin/bash

    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    REPO_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
    cd "$REPO_ROOT" || exit 1
    echo "Running lint-staged for React..."
    (cd frontend && npx lint-staged) || exit 1
    echo "Running Python linters and static type checks..."
    pre-commit run --config .pre-commit-config.yaml || exit 1
    echo "Checking Rust code formatting..."
    (cd frontend/src-tauri && cargo fmt) || exit 1
    echo "All linting and type checks passed."
