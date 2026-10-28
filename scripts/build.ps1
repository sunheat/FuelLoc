$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path .venv\Scripts\python.exe)) {
    python -m venv .venv
}
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --onefile --name FuelLoc --add-data 'src/templates;templates' --add-binary '.venv/Lib/site-packages/pytun_pmd3/wintun/bin/amd64/wintun.dll;pytun_pmd3/wintun/bin/amd64' --recursive-copy-metadata pymobiledevice3 src/main.py
