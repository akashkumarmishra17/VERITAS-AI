@echo off
title VERITAS AI Launcher
color 0A

echo ==================================
echo       VERITAS AI STARTING
echo ==================================

cd /d "%~dp0"

if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\anaconda3\Scripts\activate.bat" veritas
) else if exist "%LOCALAPPDATA%\anaconda3\Scripts\activate.bat" (
    call "%LOCALAPPDATA%\anaconda3\Scripts\activate.bat" veritas
) else (
    where conda >nul 2>nul && call conda activate veritas
)

if not exist app.py (
    echo ERROR: app.py not found!
    pause
    exit /b 1
)

echo Starting VERITAS AI Forensic System...
python -m streamlit run app.py

pause
