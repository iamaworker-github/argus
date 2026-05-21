#!/usr/bin/env bash
# Argus CI/CD scan script
# Usage: ARGUS_TARGET=./my-app ./scripts/ci-scan.sh

set -euo pipefail

TARGET="${ARGUS_TARGET:-.}"
MODE="${ARGUS_MODE:-pentest}"
OUTPUT="${ARGUS_OUTPUT:-./argus_results}"
FORMAT="${ARGUS_FORMAT:-sarif}"
LLM_KEY="${LLM_API_KEY:-}"

echo "=== Argus CI Scan ==="
echo "Target: $TARGET"
echo "Mode: $MODE"
echo "Output: $OUTPUT"
echo "Format: $FORMAT"

# Install if needed
if ! command -v argus &>/dev/null; then
    echo "Installing Argus..."
    pip install -r requirements.txt -q
    pip install -e . -q
fi

ARGS="--target $TARGET --mode $MODE --non-interactive --output $OUTPUT --format $FORMAT"

# Diff-scope for PRs
if [[ -n "${GITHUB_BASE_REF:-}" ]]; then
    ARGS="$ARGS --scope-mode diff --diff-base origin/$GITHUB_BASE_REF"
fi

if [[ -n "$LLM_KEY" ]]; then
    export LLM_API_KEY="$LLM_KEY"
fi

# Run scan
argus strix $ARGS

echo "=== Scan Complete ==="
echo "Results in: $OUTPUT"
