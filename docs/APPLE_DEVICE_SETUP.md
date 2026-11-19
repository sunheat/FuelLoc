# Apple device support on Windows

FuelLoc needs Apple's USB device drivers and a reachable Apple device service before it can connect to an iPhone. The release has been checked with Apple Mobile Device Support, included with iTunes. FuelLoc's startup screen checks the service and connected devices; it does not install or repair system components.

## Start with Apple's maintained instructions

- **Missing Apple software or drivers:** use Apple's [Windows downloads guide](https://support.apple.com/en-ca/118290). It links to the current Apple Devices and iTunes downloads and explains their roles. Install software through Apple's linked official channels rather than a standalone driver download from an unknown site.
- **The PC cannot see the phone:** follow Apple's [device-recognition troubleshooting](https://support.apple.com/en-us/108643) for USB cables, ports, and trusting the computer. First check that Apple's own software recognizes the unlocked iPhone. That establishes USB recognition; it does not by itself prove FuelLoc's Developer Mode or location connection is ready.
- **iTunes reports that Apple Mobile Device Service is not running:** follow Apple's [AMDS restart guide](https://support.apple.com/en-la/102347).

Use Apple's official downloads and installation instructions. Confirm that FuelLoc can reach the Apple device service and list the trusted USB phone. An existing working Apple setup does not need replacing just to run FuelLoc.

After installation or repair, reconnect and unlock the phone, accept its trust prompt, and choose **Recheck** in FuelLoc's setup window or **Refresh** in the workspace. Enable Developer Mode on the phone and follow its confirmation/restart prompts before connecting for location testing.

## Changing an active simulated location

Choose another point and press **Simulate Location** again. FuelLoc restores the previous simulation before setting the new coordinates while keeping the device connected. A successful replacement shows one **Location set** dialog. If restoration or setting fails, FuelLoc reports the error. The phone may briefly use its real GPS location between simulations.

If Apple Maps remains centered on the previous place, tap its current-location button to recenter before checking the location dot.

## Why FuelLoc does not install drivers for you

This is a deliberate separation of responsibilities. Installing a USB driver or changing a Windows service is a system-wide setup operation that may require administrator permission. FuelLoc leaves those changes to Apple's installer and Windows, so normal location testing can run under a standard Windows user without an administrator prompt.

FuelLoc's current connection uses an in-process userspace tunnel, replacing the original administrator-only Windows tunnel. It does not create a virtual network adapter or automatically install a driver. The bundled `wintun.dll` is retained for a transitive dependency; this connection path does not use it to create an adapter. See the [security review](../SECURITY_AUDIT.md).

Running FuelLoc as administrator is not a substitute for installing Apple's required device support. Complete any necessary system setup separately, then run FuelLoc normally. The workspace remains available for browsing when the local app is ready even if a phone prerequisite is missing.
