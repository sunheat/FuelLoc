$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$distributionExe = Join-Path (Get-Location).Path 'dist\FuelLoc\FuelLoc.exe'
$runningApps = Get-CimInstance Win32_Process -Filter "Name = 'FuelLoc.exe'" | Where-Object ExecutablePath -EQ $distributionExe
if ($runningApps) {
    throw "Choose Exit in the running FuelLoc app before rebuilding (processes: $($runningApps.ProcessId -join ', ')). The existing distribution has not been changed."
}
if (-not (Test-Path .venv\Scripts\python.exe)) {
    python -m venv .venv
}
if (-not (Test-Path '.venv\Lib\site-packages\pip')) {
    .venv\Scripts\python.exe -m ensurepip --upgrade
}
.venv\Scripts\python.exe -c "import sys, struct; assert sys.platform == 'win32' and sys.version_info[:2] == (3, 12) and struct.calcsize('P') == 8, 'Build with Python 3.12 x64 on Windows'"
if ($LASTEXITCODE -ne 0) { throw 'Unsupported build environment' }
.venv\Scripts\python.exe -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
# IPython and traitlets are only used by the optional device CLI shell.
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm --onedir --windowed --name FuelLoc --icon src/static/fuelloc.ico --version-file packaging/windows-version-info.txt --exclude-module IPython --exclude-module traitlets --add-data 'src/templates;templates' --add-data 'src/static;static' --add-binary '.venv/Lib/site-packages/pytun_pmd3/wintun/bin/amd64/wintun.dll;pytun_pmd3/wintun/bin/amd64' --recursive-copy-metadata pymobiledevice3 src/launcher.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
$exeBytes = [System.IO.File]::ReadAllBytes((Resolve-Path dist\FuelLoc\FuelLoc.exe))
$peOffset = [System.BitConverter]::ToInt32($exeBytes, 0x3c)
$subsystem = [System.BitConverter]::ToUInt16($exeBytes, $peOffset + 24 + 68)
if ($subsystem -ne 2) { throw 'FuelLoc.exe is not a Windows GUI application' }
Copy-Item LICENSE dist\FuelLoc\LICENSE
.venv\Scripts\python.exe -c "import shutil, sys; from pathlib import Path; from importlib.metadata import distribution; shutil.copyfile(Path(sys.base_prefix) / 'LICENSE.txt', 'dist/FuelLoc/PYTHON_LICENSE.txt'); shutil.copyfile(distribution('pyinstaller').locate_file('pyinstaller-6.17.0.dist-info/licenses/COPYING.txt'), 'dist/FuelLoc/PYINSTALLER_LICENSE.txt'); shutil.copyfile('.venv/Lib/site-packages/pytun_pmd3/wintun/LICENSE.txt', 'dist/FuelLoc/WINTUN_LICENSE.txt')"
if ($LASTEXITCODE -ne 0) { throw 'Cannot copy runtime license notices' }
