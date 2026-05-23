@echo off
title Setup Web Dashboard

echo ====================================================
echo   SETUP WEB DASHBOARD - Vehicle Management V1.0
echo ====================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found on this machine!
    echo.
    echo Please download Python at:
    echo   https://www.python.org/downloads/
    echo Select Python 3.11 or newer.
    echo Check "Add Python to PATH" during install.
    echo.
    echo Then run this file again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Found %PY_VER%
echo.

:: Install libraries
echo [1/3] Installing Flask...
pip install flask --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install flask!
    pause
    exit /b 1
)
echo [OK] Flask installed

echo [2/3] Installing Pandas...
pip install pandas --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install pandas!
    pause
    exit /b 1
)
echo [OK] Pandas installed

echo [3/3] Installing OpenPyXL...
pip install openpyxl --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install openpyxl!
    pause
    exit /b 1
)
echo [OK] OpenPyXL installed

echo.
echo ====================================================
echo   SETUP COMPLETE! Web Dashboard is ready to use.
echo ====================================================
echo.

set /p OPEN="Open VehicleManagement now? (Y/N): "
if /i "%OPEN%"=="Y" (
    if exist "VehicleManagement.exe" (
        echo Starting VehicleManagement.exe...
        start "" "VehicleManagement.exe"
    ) else (
        echo [WARNING] VehicleManagement.exe not found in this folder.
    )
)

echo.
pause
