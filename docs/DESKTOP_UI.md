# Desktop workspace

FuelLoc places device and fuel controls beside a flexible map. Address or coordinate search sits above the map, with **Saved places** beside Search. Location actions remain at the bottom of the sidebar. Additional map tools are available under **More map tools**.

## Window and scaling

The native app window supports resizing and maximizing. It opens at up to 1200 x 780 logical pixels, with a 32-pixel margin inside the Windows work area. Thread-local DPI virtualization accounts for display scaling and the taskbar without changing process DPI awareness.

The layout targets 1920 x 1080 or larger displays and accommodates content viewports down to 960 x 600. Below 680 pixels of content height, supplementary help text disappears while controls stay visible. Below the 760 x 580 layout floor, scrolling keeps controls accessible.

Ordinary wheel gestures do not zoom the map. Ctrl + wheel and the map zoom buttons do. Double-click selects a point without zooming. A `ResizeObserver` updates Leaflet's cached dimensions when its container changes size.

## Feedback and interaction

Location actions show a modal result dialog after the device endpoint confirms success. **Location set** closes after six seconds; **Location restored** closes after three seconds. A border around OK indicates the remaining time. Hovering OK or the optional support link pauses dismissal; leaving resumes it. OK and Escape dismiss immediately.

Connection and disconnect success show a four-second notification at the bottom-right of the map. Errors require acknowledgement and provide recovery guidance with expandable technical details rendered as plain text. Pending location requests disable the simulate, stop, and disconnect buttons to prevent duplicate actions. Keyboard movement and route playback retain silent-success behavior.

Support links open separately with `noopener noreferrer`. The local workspace does not load payment scripts or payment frames.

Saved places supports previewing, naming, and deleting points. The collection holds up to 30 locations with named-place protection; see [LOCAL_STATE.md](LOCAL_STATE.md). Disabled device selectors retain readable colors in both themes. Arrow keys in editing controls do not move the map pin.

A brief Ctrl + scroll hint appears when scrolling over the map. Ctrl + wheel and Ctrl + plus/minus/zero do not change page zoom; Windows display scaling remains native. App chrome suppresses the browser context menu while text fields retain editing menus and map objects retain their own menus.

## Browser and security

FuelLoc uses an Edge or Chrome app window. Developer tools remain available. Loopback binding, Host and cross-origin write checks, and coordinate validation enforce the local HTTP boundary; see [SECURITY_AUDIT.md](../SECURITY_AUDIT.md).

## Validation

See [BUILDING.md](BUILDING.md) for unit, JavaScript, and desktop acceptance commands. Desktop acceptance uses installed Microsoft Edge and the Flask-rendered template with simulated device, fuel, and geocoding responses and a temporary database. It covers layout sizes, themes, map gestures, device selection, action feedback, and saved places without changing a physical phone or existing user data.
