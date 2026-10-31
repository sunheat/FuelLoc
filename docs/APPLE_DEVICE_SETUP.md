# Apple device support on Windows

FuelLoc 1.0.0 needs Apple's USB device drivers and a reachable Apple device service before it can connect to an iPhone. The release has been checked with Apple Mobile Device Support, included with iTunes. FuelLoc's startup screen checks the service and connected devices; it does not install or repair system components.

## Start with Apple's maintained instructions

- **Missing Apple software or drivers:** use Apple's [Windows downloads guide](https://support.apple.com/en-ca/118290). It links to the current Apple Devices and iTunes downloads and explains their roles. Install software through Apple's linked official channels rather than a standalone driver download from an unknown site.
- **The PC cannot see the phone:** follow Apple's [device-recognition troubleshooting](https://support.apple.com/en-us/108643) for USB cables, ports, and trusting the computer. First check that Apple's own software recognizes the unlocked iPhone. That establishes USB recognition; it does not by itself prove FuelLoc's Developer Mode or location connection is ready.
- **iTunes reports that Apple Mobile Device Service is not running:** follow Apple's [AMDS restart guide](https://support.apple.com/en-la/102347).

These links delegate changing download locations and installation steps to Apple. Apple's current guidance may recommend Apple Devices; FuelLoc has not separately verified every Apple software or driver distribution. For this release, the decisive checks are that FuelLoc reports its Apple device service as reachable and can list the trusted USB phone. An existing working Apple setup does not need replacing just to run FuelLoc.

After installation or repair, reconnect and unlock the phone, accept its trust prompt, and choose **Recheck** in FuelLoc's setup window or **Refresh** in the workspace. Enable Developer Mode on the phone and follow its confirmation/restart prompts before connecting for location testing.

## Why FuelLoc does not install drivers for you

This is a deliberate separation of responsibilities. Installing a USB driver or changing a Windows service is a system-wide setup operation that may require administrator permission. FuelLoc leaves those changes to Apple's installer and Windows, so normal location testing can run under a standard Windows user without an administrator prompt.

FuelLoc's current connection uses an in-process userspace tunnel, replacing the original administrator-only Windows tunnel. It does not create a virtual network adapter or automatically install a driver. The bundled `wintun.dll` is retained for a transitive dependency; this connection path does not use it to create an adapter. See the [security review](../SECURITY_AUDIT.md).

Running FuelLoc as administrator is not a substitute for installing Apple's required device support. Complete any necessary system setup separately, then run FuelLoc normally. The workspace remains available for browsing when the local app is ready even if a phone prerequisite is missing.
