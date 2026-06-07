$ErrorActionPreference = "Stop"

python -m pip install -r requirements.txt

python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name SeleniumWindowRunner `
  selenium_ui_app.py

Write-Host ""
Write-Host "Build xong:"
Write-Host "dist\SeleniumWindowRunner.exe"
