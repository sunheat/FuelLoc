# FuelLoc

FuelLoc is a portable Windows fork of [GeoPort](https://github.com/davesc63/GeoPort) for iOS location testing and browsing Australian fuel prices. It is distributed under the original project's GPLv3 license.

## Run the portable app

Download or build `FuelLoc.exe`, then double-click it. A browser window opens to the local FuelLoc interface. No installation or administrator elevation is requested by FuelLoc.

To build it yourself, install Python 3.12 and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

The output is `dist/FuelLoc.exe`. The EXE extracts its runtime into a temporary folder while running. You need Apple's Mobile Device Support (included with iTunes), a trusted USB connection, and Developer Mode enabled on the device. The Windows iOS 17+ path uses an in-process userspace tunnel; it does not create a virtual network adapter. A real iPhone running iOS 18.7.7 connected and disconnected through the userspace tunnel under a standard-user process. A short set-and-clear test at a user-selected address succeeded through the portable EXE.

The map and fuel-price feed need Internet access. Fuel-price requests go to `projectzerothree.info`; map tiles and search use third-party map services. FuelLoc does not send device identifiers to GeoPort's telemetry endpoint. External JavaScript is pinned with Subresource Integrity. See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for the source review and its limits.

The original GeoPort [FAQ](FAQ.md) and project history remain available for reference.
