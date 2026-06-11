#!/usr/bin/env bash
# Deploy from the dev machine to the Jetson over SSH (run from repo root or scripts/).
# Usage: scripts/deploy.sh [host]   (default: abhigya@abhigya-orin)
set -euo pipefail

HOST="${1:-abhigya@abhigya-orin}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_DIR="~/remy"

echo "deploying to $HOST:$REMOTE_DIR"
ssh "$HOST" "mkdir -p $REMOTE_DIR"

# manifest of what this deploy contains, so the remote can prune deleted files
(cd "$REPO_DIR" && git ls-files > .deploy-manifest)

# tar over ssh — rsync isn't on Windows Git Bash by default
(cd "$REPO_DIR" && git ls-files -z; cd "$REPO_DIR" && git ls-files -z --others --exclude-standard) \
    | (cd "$REPO_DIR" && tar -cz --null -T -) \
    | ssh "$HOST" "tar -xz -C $REMOTE_DIR"
rm -f "$REPO_DIR/.deploy-manifest"

# prune files deleted upstream, then commit (remote stays a git repo so
# self-iteration can commit and roll back)
ssh "$HOST" "cd $REMOTE_DIR && git init -q -b main 2>/dev/null || true; \
             git ls-files | grep -vxF -f .deploy-manifest | xargs -r rm -f; \
             git add -A && git -c user.name=deploy -c user.email=deploy@local \
             commit -qm 'deploy: $(date -u +%Y-%m-%dT%H:%M:%SZ)' || true"
echo "done."
