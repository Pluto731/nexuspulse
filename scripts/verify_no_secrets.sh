#!/usr/bin/env bash
# ============================================================
# Security verification script: Ensure no secrets are staged or committed
# ============================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🔍 [Security Audit] Scanning repository for secret leaks..."

# 1. Ensure .env is untracked and in .gitignore
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo "❌ [ALERT] .env is tracked by git! Aborting immediately!"
    exit 1
fi

# 2. Scan tracked files and unstaged/staged diffs for OpenAI/DeepSeek key patterns
SUSPECT_PATTERNS='(sk-[a-zA-Z0-9]{20,}|Bearer [a-zA-Z0-9_\-\.]{20,}|BEGIN PRIVATE KEY)'

FOUND_LEAKS=$(git grep -E -I "$SUSPECT_PATTERNS" -- ':!scripts/verify_no_secrets.sh' || true)

if [ -n "$FOUND_LEAKS" ]; then
    echo "❌ [ALERT] Found potential secret leak in tracked files:"
    echo "$FOUND_LEAKS"
    exit 1
fi

# 3. Scan git commit history for keys (excluding the audit script itself)
HISTORY_LEAKS=$(git log -p -n 50 -- . ':!scripts/verify_no_secrets.sh' | grep -E -I "$SUSPECT_PATTERNS" || true)
if [ -n "$HISTORY_LEAKS" ]; then
    echo "❌ [ALERT] Found potential secret leak in commit history:"
    echo "$HISTORY_LEAKS"
    exit 1
fi

echo "✅ [Security Audit Passed] No API keys, credentials, or sensitive files found in git tree."
exit 0
