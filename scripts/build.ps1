$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path .venv\Scripts\python.exe)) {
    python -m venv .venv
}
if (-not (Test-Path '.venv\Lib\site-packages\pip')) {
    .venv\Scripts\python.exe -m ensurepip --upgrade
}
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
# IPython and traitlets are only used by the optional device CLI shell.
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --onedir --windowed --name FuelLoc --exclude-module IPython --exclude-module traitlets --add-data 'src/templates;templates' --add-binary '.venv/Lib/site-packages/pytun_pmd3/wintun/bin/amd64/wintun.dll;pytun_pmd3/wintun/bin/amd64' --recursive-copy-metadata pymobiledevice3 src/launcher.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
$exeBytes = [System.IO.File]::ReadAllBytes((Resolve-Path dist\FuelLoc\FuelLoc.exe))
$peOffset = [System.BitConverter]::ToInt32($exeBytes, 0x3c)
$subsystem = [System.BitConverter]::ToUInt16($exeBytes, $peOffset + 24 + 68)
if ($subsystem -ne 2) { throw 'FuelLoc.exe is not a Windows GUI application' }
Copy-Item LICENSE dist\FuelLoc\LICENSE
