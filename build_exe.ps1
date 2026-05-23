# ============================================================
#  build_exe.ps1 — Build script cho VehicleManagement EXE
#  Chạy: .\build_exe.ps1
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  BUILD: Phan mem Quan ly Xe V1.0          " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# ─────────────────────────────────────
# 1. Kiểm tra PyInstaller đã cài chưa
# ─────────────────────────────────────
Write-Host "`n[1/5] Kiem tra PyInstaller..." -ForegroundColor Yellow
try {
    pyinstaller --version | Out-Null
    Write-Host "      OK: PyInstaller da duoc cai dat." -ForegroundColor Green
} catch {
    Write-Host "      Chua co PyInstaller. Dang cai dat..." -ForegroundColor Red
    pip install pyinstaller
}

# ─────────────────────────────────────
# 2. Dọn dẹp thư mục build cũ
# ─────────────────────────────────────
Write-Host "`n[2/5] Don dep thu muc build cu..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build"; Write-Host "      Xoa: build/" }
if (Test-Path "dist")  { Remove-Item -Recurse -Force "dist";  Write-Host "      Xoa: dist/"  }
Write-Host "      Xong." -ForegroundColor Green

# ─────────────────────────────────────
# 3. Chạy PyInstaller
# ─────────────────────────────────────
Write-Host "`n[3/5] Dang build EXE (co the mat 3-5 phut)..." -ForegroundColor Yellow
pyinstaller vehicle_management.spec --clean --noconfirm

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[LOI] PyInstaller that bai! Kiem tra log o tren." -ForegroundColor Red
    exit 1
}
Write-Host "      Build thanh cong!" -ForegroundColor Green

# ─────────────────────────────────────
# 4. Tạo thư mục phân phối (dist package)
# ─────────────────────────────────────
Write-Host "`n[4/5] Tao goi phan phoi..." -ForegroundColor Yellow

$version   = "v1.0"
$pkgName   = "VehicleManagement_$version"
$pkgDir    = "dist\$pkgName"

# Tạo cấu trúc thư mục phân phối
New-Item -ItemType Directory -Force -Path $pkgDir | Out-Null

# Copy EXE chính
Copy-Item "dist\VehicleManagement.exe" "$pkgDir\VehicleManagement.exe"
Write-Host "      [OK] VehicleManagement.exe"

# Copy dashboard_api.py (Flask server — PHẢI đặt cùng thư mục với EXE)
if (Test-Path "dashboard_api.py") {
    Copy-Item "dashboard_api.py" "$pkgDir\dashboard_api.py"
    Write-Host "      [OK] dashboard_api.py"
} else {
    Write-Host "      [CANH BAO] Khong tim thay dashboard_api.py!" -ForegroundColor Yellow
}

# Copy dashboard.html (giao diện React)
if (Test-Path "dashboard.html") {
    Copy-Item "dashboard.html" "$pkgDir\dashboard.html"
    Write-Host "      [OK] dashboard.html"
} else {
    Write-Host "      [CANH BAO] Khong tim thay dashboard.html!" -ForegroundColor Yellow
}

# Copy thư mục assets (logo, fonts)
if (Test-Path "assets") {
    Copy-Item -Recurse "assets" "$pkgDir\assets"
    Write-Host "      [OK] assets/"
}

# Copy hướng dẫn sử dụng
if (Test-Path "HUONG_DAN_DASHBOARD.txt") {
    Copy-Item "HUONG_DAN_DASHBOARD.txt" "$pkgDir\HUONG_DAN_DASHBOARD.txt"
}
if (Test-Path "User_Guide.md") {
    Copy-Item "User_Guide.md" "$pkgDir\User_Guide.md"
}

Write-Host "      Thu muc phan phoi: $pkgDir" -ForegroundColor Green

# ─────────────────────────────────────
# 5. Nén thành file ZIP
# ─────────────────────────────────────
Write-Host "`n[5/5] Nen thanh file ZIP..." -ForegroundColor Yellow
$zipPath = "dist\${pkgName}.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath }

Compress-Archive -Path "$pkgDir\*" -DestinationPath $zipPath
Write-Host "      Tao file: $zipPath" -ForegroundColor Green

# ─────────────────────────────────────
# Tóm tắt kết quả
# ─────────────────────────────────────
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  BUILD HOAN THANH!                        " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$exeSize = (Get-Item "dist\VehicleManagement.exe").length / 1MB
$zipSize = (Get-Item $zipPath).length / 1MB
Write-Host "  EXE : dist\VehicleManagement.exe  ($([math]::Round($exeSize,1)) MB)" -ForegroundColor White
Write-Host "  ZIP : $zipPath  ($([math]::Round($zipSize,1)) MB)" -ForegroundColor White
Write-Host ""
Write-Host "  => Gui file ZIP nay cho nguoi dung." -ForegroundColor Green
Write-Host ""
