#!/usr/bin/env bash
# REMY installer — run ON the Jetson (Orin Nano, JetPack r36, Ubuntu 22.04).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${REMY_VENV:-$HOME/.remy/venv}"
VOICES_DIR="$HOME/.remy/voices"
VOICE="${REMY_VOICE:-en_GB-alan-medium}"

echo "== REMY install =="
echo "repo: $REPO_DIR"

# --- python venv + package ---
mkdir -p "$HOME/.remy"
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
    echo ">> then on this Jetson:"
    echo ">>   echo 'CLAUDE_CODE_OAUTH_TOKEN=<token>' >> ~/.remy/env"
    echo ">>   echo 'export CLAUDE_CODE_OAUTH_TOKEN=<token>' >> ~/.bashrc"
fi

# --- whisper model warmup (downloads on first use otherwise) ---
python3 - <<'EOF'
from faster_whisper import WhisperModel
WhisperModel("base", device="cpu", compute_type="int8")
print("whisper base ready")
EOF

echo
echo "== done =="
echo "run:        $VENV/bin/python -m remy"
echo "headless:   $VENV/bin/python -m remy --headless"
echo "service:    sudo cp scripts/remy.service /etc/systemd/system/ && sudo systemctl enable --now remy"
echo "dashboard:  http://$(hostname -I | awk '{print $1}'):8484"
