$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$sourceCommit = git rev-parse HEAD
if ($LASTEXITCODE -ne 0) { throw 'Package from a Git checkout' }
$changes = git status --porcelain
if ($LASTEXITCODE -ne 0 -or $changes) { throw 'Commit all source changes before packaging a release' }
$versionMatch = Select-String -Path src/main.py -Pattern '^APP_VERSION = "(\d+\.\d+\.\d+)"$'
if (-not $versionMatch) { throw 'Cannot read APP_VERSION' }
$releaseVersion = $versionMatch.Matches[0].Groups[1].Value
$releaseNotes = "docs/releases/$releaseVersion.md"
if (-not (Test-Path -LiteralPath $releaseNotes)) { throw "Missing release notes: $releaseNotes" }

& ./scripts/build.ps1
$exeVersion = (Get-Item dist/FuelLoc/FuelLoc.exe).VersionInfo
if ($exeVersion.ProductVersion -ne $releaseVersion -or $exeVersion.FileVersion -ne $releaseVersion) {
    throw 'Windows executable metadata must match APP_VERSION'
}
Copy-Item docs/PORTABLE_README.txt dist/FuelLoc/README.txt
Copy-Item $releaseNotes dist/FuelLoc/RELEASE_NOTES.md
Copy-Item THIRD_PARTY_NOTICES.md dist/FuelLoc/THIRD_PARTY_NOTICES.md
$resolvedPackages = .venv/Scripts/python.exe -m pip freeze
if ($LASTEXITCODE -ne 0) { throw 'Cannot record resolved dependencies' }
$resolvedPackages | Set-Content -Encoding UTF8 dist/FuelLoc/requirements-resolved.txt
$pythonVersion = .venv/Scripts/python.exe --version
if ($LASTEXITCODE -ne 0) { throw 'Cannot read Python version' }
@"
FuelLoc $releaseVersion - Windows x64
Source commit: $sourceCommit
Source: https://github.com/sunheat/FuelLoc/tree/$sourceCommit
$pythonVersion
Build command: powershell -ExecutionPolicy Bypass -File scripts/package.ps1
Dependency versions: requirements-resolved.txt
"@ | Set-Content -Encoding UTF8 dist/FuelLoc/BUILD-INFO.txt

New-Item -ItemType Directory -Force dist/release | Out-Null
$portableArchive = "dist/release/FuelLoc-$releaseVersion-windows-x64.zip"
$sourceArchive = "dist/release/FuelLoc-$releaseVersion-source.zip"
git archive --format=zip "--prefix=FuelLoc-$releaseVersion-source/" "--output=$sourceArchive" $sourceCommit
if ($LASTEXITCODE -ne 0) { throw 'Source archive failed' }
Compress-Archive -Path dist/FuelLoc -DestinationPath $portableArchive -Force
@($portableArchive, $sourceArchive) | ForEach-Object {
    $archiveHash = Get-FileHash -LiteralPath $_ -Algorithm SHA256
    '{0}  {1}' -f $archiveHash.Hash.ToLowerInvariant(), (Split-Path -Leaf $_)
} | Set-Content -Encoding ASCII dist/release/SHA256SUMS.txt
Write-Host "Release files prepared in dist/release for source commit $sourceCommit. Nothing has been published."
