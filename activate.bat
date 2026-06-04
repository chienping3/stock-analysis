@echo off
echo ========================================
echo   Stock Analyzer - Starting Service
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [3/4] Installing dependencies...
pip install -q flask

REM Start service
echo [4/4] Starting server...
echo.
echo ========================================
echo   Server is running!
echo   Open browser: http://localhost:8080
echo   For phone: http://YOUR_PC_IP:8080
echo ========================================
echo.

python app.py

pause
