#!/usr/bin/env bash
# Deploy from the dev machine to the Jetson over SSH (run from repo root or scripts/).
# Usage: scripts/deploy.sh [host]   (default: abhigya@abhigya-orin)
set -euo pipefail

HOST="${1:-abhigya@abhigya-orin}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_DIR="~/jetsonclaw"

echo "deploying to $HOST:$REMOTE_DIR"
ssh "$HOST" "mkdir -p $REMOTE_DIR"
# tar over ssh — rsync isn't on Windows Git Bash by default
(cd "$REPO_DIR" && git ls-files -z; cd "$REPO_DIR" && git ls-files -z --others --exclude-standard) \
    | (cd "$REPO_DIR" && tar -cz --null -T -) \
    | ssh "$HOST" "tar -xz -C $REMOTE_DIR"

# keep the remote a git repo so self-iteration can commit/rollback
ssh "$HOST" "cd $REMOTE_DIR && git init -q -b main 2>/dev/null || true; \
             git add -A && git -c user.name=deploy -c user.email=deploy@local \
             commit -qm 'deploy: $(date -u +%Y-%m-%dT%H:%M:%SZ)' || true"
echo "done."
