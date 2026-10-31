# Building FuelLoc

## Windows development build

Use Windows x64, Git, and Python **3.12 x64** with Tcl/Tk support (the normal python.org installer includes it). Confirm `python --version` reports 3.12 before running the script. Runtime browser and Apple prerequisites are listed in the [README](../README.md).

```powershell
git clone https://github.com/sunheat/FuelLoc.git
cd FuelLoc
# For the published 1.0.0 source, select its tag after release:
# git checkout v1.0.0
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

The script creates `.venv` if needed, installs `requirements-build.txt`, and runs PyInstaller. Output is **`dist/FuelLoc/`**. Start `dist/FuelLoc/FuelLoc.exe`; keep its `_internal` directory beside it. `build/FuelLoc/FuelLoc.exe` is an intermediate file and is not runnable on its own. Choose **Exit** in an existing distribution before rebuilding; the script refuses to overwrite a running copy at that path.

Direct build dependencies are pinned. Transitive dependencies may change between builds; release archives include `requirements-resolved.txt` and `BUILD-INFO.txt` to record the actual environment and source commit. Byte-for-byte reproducibility is not promised. The generated `FuelLoc.spec`, build outputs, virtual environment, and local agent settings are excluded from source control.

## Validation

Run the checks from the repository root after installing build dependencies:

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
node tests/test_connect_ui.js
node tests/test_fuel_preferences.js
node tests/test_location_feedback.js
.venv\Scripts\python.exe -m pip install playwright
.venv\Scripts\python.exe tests/desktop_acceptance.py
```

The JavaScript checks require Node.js. Desktop acceptance requires installed Microsoft Edge and Internet access for pinned interface libraries. It intercepts phone, fuel, and geocoding requests, uses temporary saved-place data, and writes screenshots under `build/`. These checks do not verify a physical iPhone. Keep Playwright out of the runtime requirements.

## Release archives

From a clean, committed checkout of the intended source revision:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/package.ps1
```

This rebuilds the app and creates the following in `dist/release/`:

- `FuelLoc-1.0.0-windows-x64.zip`: the complete `FuelLoc/` folder, executable, runtime, license, dependency notices, user instructions, release notes, and build information.
- `FuelLoc-1.0.0-source.zip`: tracked source at the recorded commit, including build scripts and license. Local configuration and user data are excluded.
- `SHA256SUMS.txt`: SHA-256 hashes of both archives.

Version names come from `APP_VERSION` in `src/main.py`. Windows executable metadata in `packaging/windows-version-info.txt` must match. No script creates a tag, creates a GitHub Release, uploads files, signs the EXE, or publishes anything.

Extract the portable archive into a fresh folder and test that copy before publication. To compare a download with `SHA256SUMS.txt`:

```powershell
Get-FileHash .\FuelLoc-1.0.0-windows-x64.zip -Algorithm SHA256
```

Release publication is a separate, manual maintainer action after the [release checklist](RELEASE_CHECKLIST.md) and owner approval. Attach both archives and `SHA256SUMS.txt` to a release at the matching source commit.

## macOS, Linux, and GitHub Actions

FuelLoc 1.0.0 supports a Windows x64 distribution only. Its Tk icon setup, browser discovery, Apple device-service check, and build script assume Windows. Running PyInstaller on another system alone does not port or validate these paths. There is no supported macOS/Linux build command for this release.

[PyInstaller is not a cross-compiler](https://pyinstaller.org/en/stable/): build each supported platform on that platform. GitHub Actions can provide Windows, Linux, and macOS machines without owning those computers. [Standard GitHub-hosted runners are free for public repositories](https://docs.github.com/en/actions/concepts/billing-and-usage); larger runners and private-repository usage have different billing rules. Artifact storage has separate limits, so a future workflow should use short retention and review account budgets before storing large builds. This release does not require paid signing, a hosted build service, or an Actions workflow.

Before offering other-platform binaries, adapt the platform-specific paths, build on native runners, and verify startup and a real-device set/clear cycle on each claimed platform. A successful CI build alone is insufficient evidence of iPhone compatibility.
