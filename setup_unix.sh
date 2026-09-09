#!/usr/bin/env bash
# setup_unix.sh — J.A.R.V.I.S. v6.1 setup for Linux and macOS
set -e
OS="$(uname -s)"
echo ""; echo "============================================================"
echo "  J.A.R.V.I.S. v6.1  —  Setup ($OS)"; echo "============================================================"; echo ""

if [ "$OS" = "Linux" ]; then
    echo "Installing system dependencies..."
    sudo apt-get update -qq
    sudo apt-get install -y build-essential cmake portaudio19-dev \
        python3-dev python3-pip python3-venv libopencv-dev adb 2>/dev/null || true
elif [ "$OS" = "Darwin" ]; then
    command -v brew &>/dev/null || { echo "Install Homebrew: https://brew.sh"; exit 1; }
    brew install cmake portaudio opencv android-platform-tools 2>/dev/null || true
fi

[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip --quiet
echo "Installing requirements (dlib may take 5-10 min)..."
pip install -r requirements.txt

mkdir -p gmail_data
echo "Created gmail_data/ for Gmail credentials."

echo ""; echo "Verifying..."
python3 -c "import flask, psutil, requests; print('  Core: OK')" 2>/dev/null
python3 -c "import cv2, face_recognition; print('  Biometric: OK')" 2>/dev/null || echo "  Biometric: needs C++ tools"
python3 -c "import speech_recognition, pyttsx3; print('  Voice: OK')" 2>/dev/null
python3 -c "import googleapiclient; print('  Gmail: OK')" 2>/dev/null

cat > launch_jarvis.sh << 'LAUNCHER'
#!/usr/bin/env bash
source "$(dirname "$0")/venv/bin/activate"
python3 "$(dirname "$0")/jarvis_core.py"
LAUNCHER
chmod +x launch_jarvis.sh

echo ""; echo "============================================================"
echo "  Setup complete!"; echo "  1. Edit jarvis_config.json — add your free API keys"
echo "  2. For Gmail: put credentials.json in gmail_data/"
echo "  3. Run: ./launch_jarvis.sh  or  python3 jarvis_core.py"
echo "  4. Web UI: http://127.0.0.1:5000"; echo "============================================================"; echo ""

read -p "Launch JARVIS now? [Y/n]: " L
[[ "$L" =~ ^[Nn]$ ]] || ./launch_jarvis.sh
