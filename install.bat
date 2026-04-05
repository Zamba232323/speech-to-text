@echo off
echo === Speech-to-Text Installer ===
echo.

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Install Python 3.10+ and add to PATH.
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv .venv
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Running setup check...
python setup_check.py

echo.
echo === Installation complete ===
pause
