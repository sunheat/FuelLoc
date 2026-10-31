# Third-party notices

FuelLoc is derived from **GeoPort by davesc63**. FuelLoc's modified source is distributed under GNU GPL version 3; the complete text is in `LICENSE`. Matching FuelLoc source, dependency requirements, and build scripts are provided with each release.

The portable distribution includes Python, Tcl/Tk, Flask, pymobiledevice3, PyInstaller's bootloader, and transitive dependencies. These components retain their own licenses. Python, PyInstaller, and Wintun notices are included beside the EXE as `PYTHON_LICENSE.txt`, `PYINSTALLER_LICENSE.txt`, and `WINTUN_LICENSE.txt`. Dependency metadata and supplied license files are preserved under `_internal/`, including package `.dist-info` directories. `requirements-resolved.txt` records the installed Python package versions used for the build; some packages are build-time or optional dependencies rather than runtime features.

The packaged `wintun.dll` originates from the pytun-pmd3 dependency and is signed by WireGuard LLC. FuelLoc's current device connection uses pymobiledevice3's userspace tunnel and does not create a Wintun adapter. Do not remove bundled license files when redistributing the portable folder.

The map interface uses third-party libraries and services, including Leaflet and OpenStreetMap-based providers. Their source headers, resource references, and visible map attribution are retained. Externally loaded resources are not covered by FuelLoc's license merely because FuelLoc uses them. Map data and fuel-price data remain subject to their respective providers' terms.

FuelLoc's application icon was generated for this fork; see `docs/APP_ICON.md` in the source distribution for its provenance.
