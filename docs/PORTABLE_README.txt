FuelLoc 1.0.0 - Windows x64 portable app

Extract the entire ZIP, then run FuelLoc.exe inside the FuelLoc folder.
Keep the _internal folder beside the EXE. Python is not required.
The EXE is unsigned. Download only from the official FuelLoc release page:
https://github.com/sunheat/FuelLoc/releases

Requirements: Windows x64, Microsoft Edge or Google Chrome, Apple Mobile
Device Support (included with iTunes), a USB-connected trusted iPhone,
and Developer Mode enabled on the phone. Internet access is needed for maps,
search, fuel prices, and any required developer-image downloads.
Tested device: iPhone on iOS 18.7.7. Other configurations are not verified.

FuelLoc runs without an administrator prompt and does not install drivers or
create a virtual network adapter. Apple driver/service setup is deliberately
separate and may require administrator permission. Official download and
troubleshooting links are collected here:
https://github.com/sunheat/FuelLoc/blob/v1.0.0/docs/APPLE_DEVICE_SETUP.md

The original project's device telemetry, extra visit reporting, remote
broadcast/version requests, and IP-geolocation lookup have been removed.
Maps, search, routing, and fuel prices still use external services.

1. Start FuelLoc.exe. Choose Enter app once the local app is ready.
2. Unlock and trust your phone. Refresh, select it, and Connect Device.
3. Search an address or latitude, longitude; or double-click and drag a pin.
4. Simulate Location sends the selected point to the phone.
5. Stop Location clears simulation. Then Disconnect and choose Exit.

Previewing a point or saved place does not change the phone's location.
Stop simulation before unplugging. Read error details if an action fails;
reconnect and retry Stop Location if needed. Closing the browser window alone
leaves the controller running. Use Exit to shut it down cleanly.

Hold Ctrl while scrolling to zoom, or use the map's + / - buttons.
Saved places keeps up to 30 saved and recent locations; named places are
protected from automatic replacement.

Fuel prices come from projectzerothree.info and may be delayed or incomplete.
Confirm prices with the station. The feed cache expires after five minutes;
the next request refreshes it. An unchanged screen does not poll automatically.
Map/search/routing providers receive relevant network requests and your IP.

Local data: %LOCALAPPDATA%\FuelLoc\state.sqlite3
Browser profile: %LOCALAPPDATA%\FuelLoc\BrowserProfile
Back up the database while FuelLoc is closed. Replacing this portable folder
does not erase your saved places. No device connection is restored on startup.

Documentation, troubleshooting, source, and build instructions:
https://github.com/sunheat/FuelLoc#readme
BUILD-INFO.txt identifies the source commit used for this executable.
requirements-resolved.txt records the build environment's Python packages.

Derived from GeoPort by davesc63. Licensed under GPLv3; see LICENSE and
THIRD_PARTY_NOTICES.md. Provided without warranty under the license.
Optional support: https://ko-fi.com/sunheat
