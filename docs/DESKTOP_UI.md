# Desktop workspace

The previous browser page stacked full-width sections around a fixed-height map. At a 1200 × 720 content viewport, the primary location buttons required 552 pixels of page scrolling. Leaflet consumed wheel events along the way.

The workspace now uses a compact device/fuel sidebar beside a flexible map. Location input sits above the map; simulate/stop actions stay at the bottom of the sidebar. Fuel mode starts enabled, including region, fuel type, and the selected price details. The existing extra map tools remain available behind **More map tools**. Address-search behavior and the device protocol are unchanged.

## Window and scaling

Keep the native resizable app window: resizing and maximizing are useful when inspecting a map. Launch at up to 1200 × 780 logical pixels, with a 32-pixel margin inside the Windows work area. Query that area with thread-local DPI virtualization so the calculation accounts for display scaling and the taskbar without changing the process's DPI awareness.

The target is a 1920 × 1080 or larger display. Check content viewports down to 960 × 600, including reduced space representative of common 125%/150% scaling. Below 680 pixels of content height, supplementary help text disappears while the controls stay visible. Below the 760 × 580 layout floor, scrolling is a fallback; no controls are deliberately discarded to enforce a fixed window.

Ordinary wheel gestures do not zoom the map. Ctrl + wheel and the zoom buttons do. Double-click selects a point without also zooming. A ResizeObserver invalidates Leaflet's cached dimensions when its container changes size.

## References

- [Microsoft desktop layout guidance](https://learn.microsoft.com/en-us/windows/win32/uxguide/vis-layout): visual grouping, efficient use of space, and useful resizing.
- [QGIS interface](https://docs.qgis.org/testing/en/docs/user_manual/introduction/qgis_gui.html): panels alongside a central map canvas.
- [QGIS user reviews](https://www.capterra.com/p/185949/QGIS/): a well-reviewed map application used as a layout reference, rather than reproducing its full GIS toolset.
- The adjacent iOS location-track app: dark panels, compact controls, and a map that fills the remaining workspace. FuelLoc keeps a single-point default workflow.

## Repeatable checks

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
node tests\test_connect_ui.js
.venv\Scripts\python.exe -m pip install playwright
.venv\Scripts\python.exe tests\desktop_acceptance.py
```

Playwright is only a development dependency. The acceptance script uses installed Microsoft Edge, the real Flask-rendered template, and pinned external map libraries. It intercepts phone/fuel/geocoding requests so it never changes a real phone's location. It checks page/sidebar overflow at six sizes, map resizing, fuel defaults and filters, wheel gestures, connection and location actions, themes, and optional map tools. Screenshots are written under `build/`.

The disconnect test also catches a pre-existing UI-state bug: selecting fuel after disconnect previously re-enabled location buttons because the hidden connection value remained populated. Disconnect now clears that value.

Ordinary map scrolling briefly shows a translucent Ctrl + scroll hint. Holding Ctrl or leaving the map dismisses it. Ctrl + wheel and Ctrl + plus/minus/zero do not change page zoom; Windows display scaling remains native. App chrome suppresses the browser context menu while text fields retain their editing menu. Existing map-object menus remain available. The search field accepts either an address or a coordinate pair.
