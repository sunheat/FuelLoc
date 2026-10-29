# FuelLoc

FuelLoc is a portable Windows app for iOS location testing and browsing Australian fuel prices. It is based on GeoPort by davesc63 and remains licensed under GPLv3; see [LICENSE](LICENSE) for the complete license text.

## Run the portable app

Download or build the `FuelLoc` folder, then double-click `FuelLoc.exe` inside it. The prerequisite window appears while the local app starts. **Enter app** becomes available as soon as the local app is ready, even if other checks fail. FuelLoc then opens its local interface in a standalone app window without a command prompt. No installation or administrator elevation is requested by FuelLoc.

To build it yourself, install Python 3.12 and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

The output is `dist/FuelLoc/`, including `FuelLoc.exe` and `LICENSE`. Keep the entire folder together when sharing the app. You need Apple's Mobile Device Support (included with iTunes), a trusted USB connection, and Developer Mode enabled on the device. The Windows iOS 17+ path uses an in-process userspace tunnel; it does not create a virtual network adapter. A real iPhone running iOS 18.7.7 connected and disconnected through the userspace tunnel under a standard-user process. A short set-and-clear test at a user-selected address succeeded through the portable EXE.

The map and fuel-price feed need Internet access. Fuel-price requests go to `projectzerothree.info`; map tiles and search use third-party map services. FuelLoc does not send device identifiers to the original project's telemetry endpoint. External JavaScript is pinned with Subresource Integrity. See [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for the source review and its limits.

The original author's attribution is retained here as required by the GPLv3 license. The donation area in the app is reserved for a future FuelLoc account and has no payment link.
