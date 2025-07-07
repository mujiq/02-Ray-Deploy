#!/bin/bash
# Quick Test Runner - Delegates to comprehensive test runner
# Usage: ./run_tests.sh [arguments to pass to run_all_tests.py]

cd "$(dirname "$0")"
python3 tests/run_all_tests.py "$@" 