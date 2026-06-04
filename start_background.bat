@echo off

:: Stock Analysis Background Service
:: Save as UTF-8 without BOM, or ANSI with English-only text

title Stock Analysis - Background Service

cd /d "%~dp0"

echo.
echo ================================================
echo   Taiwan Stock Analysis - Background Service
echo ================================================
echo.

:: ---- Check Python ----
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)
echo [OK] Python found

:: ---- Setup venv ----
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)
echo [OK] Virtual environment ready

:: ---- Install dependencies ----
echo [INFO] Checking dependencies...
venv\Scripts\python.exe -c "import flask, apscheduler" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing dependencies...
    venv\Scripts\python.exe -m pip install -r requirements-light.txt --quiet
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)
echo [OK] Dependencies ready

:: ---- Start ----
echo.
echo ================================================
echo   Starting service...
echo   Dashboard : http://localhost:8080
echo   API Status: http://localhost:8080/api/status
echo ================================================
echo.
echo Press Ctrl+C to stop the service
echo.

venv\Scripts\python.exe app.py

pause
