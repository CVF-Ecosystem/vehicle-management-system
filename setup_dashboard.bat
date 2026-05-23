@echo off
chcp 65001 >nul
title Cài đặt Web Dashboard - Quản lý Xe V1.0

echo ====================================================
echo   CÀI ĐẶT WEB DASHBOARD - PHẦN MỀM QUẢN LÝ XE
echo ====================================================
echo.

:: ── Kiểm tra Python ──────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python tren may tinh nay!
    echo.
    echo  Vui long cai Python tai:
    echo    https://www.python.org/downloads/
    echo  (Chon Python 3.11+, tich o "Add Python to PATH")
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo [OK] Da tim thay %PY_VER%
echo.

:: ── Cài thư viện ─────────────────────────────────────
echo [1/3] Cai dat Flask...
pip install flask --quiet --disable-pip-version-check
if %errorlevel% neq 0 ( echo [LOI] Cai flask that bai! & pause & exit /b 1 )
echo [OK] Flask

echo [2/3] Cai dat Pandas...
pip install pandas --quiet --disable-pip-version-check
if %errorlevel% neq 0 ( echo [LOI] Cai pandas that bai! & pause & exit /b 1 )
echo [OK] Pandas

echo [3/3] Cai dat OpenPyXL...
pip install openpyxl --quiet --disable-pip-version-check
if %errorlevel% neq 0 ( echo [LOI] Cai openpyxl that bai! & pause & exit /b 1 )
echo [OK] OpenPyXL

echo.
echo ====================================================
echo   CAI DAT HOAN THANH!
echo   Ban co the dung Web Dashboard binh thuong roi.
echo ====================================================
echo.

:: ── Hỏi có muốn mở app ngay không ───────────────────
set /p OPEN="Mo phan mem ngay bay gio? (Y/N): "
if /i "%OPEN%"=="Y" (
    if exist "VehicleManagement.exe" (
        echo Dang mo VehicleManagement.exe...
        start "" "VehicleManagement.exe"
    ) else (
        echo [CANH BAO] Khong tim thay VehicleManagement.exe trong thu muc nay.
    )
)

echo.
pause
