$ErrorActionPreference = "Stop"
Write-Host "Activating Virtual Environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Installing PyInstaller..."
pip install pyinstaller

Write-Host "Building Executable with PyInstaller..."
# Using --onefile to create a single standalone executable.
$cmd = "pyinstaller --noconfirm --onefile --windowed " + `
       "--add-data `"assets;assets`" " + `
       "--add-data `"icons;icons`" " + `
       "--add-data `"web_dashboard.py;.`" " + `
       "main.py"

Invoke-Expression $cmd

Write-Host "Build complete! Check the 'dist' folder for main.exe."
