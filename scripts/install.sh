#!/usr/bin/env bash
# JetsonClaw installer — run ON the Jetson (Orin Nano, JetPack r36, Ubuntu 22.04).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${JETSONCLAW_VENV:-$HOME/.jetsonclaw/venv}"
VOICES_DIR="$HOME/.jetsonclaw/voices"
VOICE="${JETSONCLAW_VOICE:-en_GB-alan-medium}"

echo "== JetsonClaw install =="
echo "repo: $REPO_DIR"

# --- python venv + package ---
mkdir -p "$HOME/.jetsonclaw"
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install --upgrade pip wheel >/dev/null
pip install -e "$REPO_DIR[voice]"

# --- wake word models (downloaded post-install by openwakeword) ---
python3 - <<'EOF'
import openwakeword.utils
openwakeword.utils.download_models()
print("wake word models ready")
EOF

# --- piper voice ---
mkdir -p "$VOICES_DIR"
if [ ! -f "$VOICES_DIR/$VOICE.onnx" ]; then
    echo "downloading piper voice $VOICE..."
    python3 -m piper.download_voices "$VOICE" --data-dir "$VOICES_DIR" \
        || echo "WARN: voice download failed — TTS will be disabled until you fetch it"
fi

# --- claude code CLI (agentic brain) ---
if ! command -v claude >/dev/null 2>&1; then
    echo "installing Claude Code CLI..."
    curl -fsSL https://claude.ai/install.sh | bash
    echo
    echo ">> AUTH: on a machine WITH a browser run:  claude setup-token"
    echo ">> then on this Jetson:  echo 'export CLAUDE_CODE_OAUTH_TOKEN=<token>' >> ~/.bashrc"
fi

# --- whisper model warmup (downloads on first use otherwise) ---
python3 - <<'EOF'
from faster_whisper import WhisperModel
WhisperModel("base", device="cpu", compute_type="int8")
print("whisper base ready")
EOF

echo
echo "== done =="
echo "run:        $VENV/bin/python -m jetsonclaw"
echo "headless:   $VENV/bin/python -m jetsonclaw --headless"
echo "service:    sudo cp scripts/jetsonclaw.service /etc/systemd/system/ && sudo systemctl enable --now jetsonclaw"
echo "dashboard:  http://$(hostname -I | awk '{print $1}'):8484"
