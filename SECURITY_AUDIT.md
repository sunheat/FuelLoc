# Security review

Reviewed source: upstream commit `d38c7c550512d3d1e0e6c49de59a695d417bc5f0` in `davesc63/GeoPort`. This is a source-level review, not a proof that third-party dependencies or future network responses are harmless.

## Findings and changes

- Removed the browser-side request that sent the connected device's identifier, model, iOS version, connection type, and country to `api.geoport.me`. Removed the dormant visit-reporting function as well.
- Removed remote version and broadcast loading. One unused template used the broadcast as trusted HTML.
- Removed TLS verification bypasses and plain HTTP IP geolocation. Fuel-price requests now verify HTTPS certificates and have a timeout.
- Removed the world-writable GeoPort folder operation and process termination by name.
- Bound the control server to loopback, disabled the Flask debugger, checked the Host and cross-origin write requests, and validated coordinate ranges.
- Replaced the administrator-only TUN path with `pymobiledevice3`'s in-process `UserspaceRsdTunnel`. No driver is installed automatically. The packaged `wintun.dll` is loaded by a transitive dependency but is not used to create an adapter in this path; its Windows signature verifies as WireGuard LLC (version 0.14.1).
- Pinned external JavaScript resources using Subresource Integrity hashes and removed obsolete polyfills.

## Remaining limits

- Fuel-price requests disclose the network IP address to `projectzerothree.info`, and map tiles/search disclose it to their providers. These services are part of the current user interface.
- The app depends on third-party Python packages and pinned JavaScript. Source review does not guarantee that these components are free of vulnerabilities.
- A paired iPhone running iOS 18.7.7 was discovered and connected through the userspace tunnel in a medium-integrity Windows process, then disconnected. A short set-and-clear location test at a user-selected address returned success through the portable EXE. The clear command ran immediately afterward. The phone's on-screen location was not independently observed.
- The executable is unsigned. Windows may show a reputation warning on first use.
