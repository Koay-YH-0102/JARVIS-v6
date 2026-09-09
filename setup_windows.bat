@echo off
setlocal enabledelayedexpansion
title J.A.R.V.I.S. v6.1 Setup
color 0B

echo.
echo  ============================================================
echo   J.A.R.V.I.S. v6.1 — Windows Setup
echo  ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (echo  ERROR: Python 3.10+ not found. Download: python.org & pause & exit /b 1)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY=%%v
echo  Python %PY% detected.

:: Virtual environment
if not exist venv (echo  Creating virtual environment... & python -m venv venv)
call venv\Scripts\activate.bat

:: Upgrade pip
python -m pip install --upgrade pip --quiet

:: PyAudio (Windows-specific)
echo  Installing PyAudio...
pip install pipwin --quiet
pipwin install pyaudio --quiet 2>nul
if errorlevel 1 pip install pyaudio --quiet 2>nul

:: All requirements
echo  Installing all requirements (face_recognition may take 5-10 min)...
pip install -r requirements.txt

:: Gmail data dir
if not exist gmail_data mkdir gmail_data
echo  Created gmail_data\ folder for Gmail credentials.

:: Verify
echo.
echo  Verifying core imports...
python -c "import flask, psutil, requests; print('  Core: OK')" 2>nul
python -c "import cv2, face_recognition; print('  Biometric: OK')" 2>nul || echo   Biometric: install C++ Build Tools then retry
python -c "import speech_recognition, pyttsx3; print('  Voice: OK')" 2>nul
python -c "import googleapiclient; print('  Gmail: OK')" 2>nul

:: Launch script
echo @echo off > launch_jarvis.bat
echo title J.A.R.V.I.S. v6.1 >> launch_jarvis.bat
echo call venv\Scripts\activate >> launch_jarvis.bat
echo python jarvis_core.py >> launch_jarvis.bat
echo  Created launch_jarvis.bat

echo.
echo  ============================================================
echo   Setup complete!
echo   1. Edit jarvis_config.json — add your free API keys
echo   2. For Gmail: put credentials.json in gmail_data\
echo   3. Run: launch_jarvis.bat
echo   4. Web UI: http://127.0.0.1:5000
echo  ============================================================
echo.
set /p "L=Launch JARVIS now? [Y/n]: "
if /i not "!L!"=="n" call launch_jarvis.bat
pause
