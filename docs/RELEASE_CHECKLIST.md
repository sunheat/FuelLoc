# First release checklist

## Interaction and local data

- Merge the wheel/context-menu polish and local-preferences/saved-places PRs. Keep address and coordinate search in one field for this release.
- Run the Python unit suite, Node connection check, and Edge desktop acceptance check on the combined changes. Check normal wheel, Ctrl + wheel, keyboard zoom, context menus, and keyboard editing.
- Verify Windows display scaling at 125% and 150% on a real desktop. Automated viewport checks exercise available layout space; they do not replace a native DPI check.
- Keep the first region as All Australia, then remember user selection. IP-based defaults are deferred; no new lookup service or location permission is needed.

## Distribution

- Build the complete portable folder and test a newly extracted copy on a Windows account without the development environment.
- Check EXE, setup window, workspace header, and browser app-window icons. Browser taskbar grouping remains browser-owned.
- Test missing Apple device support, no phone, no Internet, a busy local port, and closing/reopening the app. Keep setup errors readable and entry available when the local app is ready.
- Before publishing, perform a short real-device connect, simulate, stop, disconnect, and exit check. Automated acceptance uses mocks and does not exercise a physical phone.
- Publish a matching source revision with the release and retain LICENSE and upstream attribution. Confirm the archive includes the entire `_internal` folder.
- Merge the fuel-cache expiry fix, then verify the live feed's available regions, timestamps, and freshness after leaving the app open. The fix refreshes the cache on the next fuel request after five minutes; the displayed price does not poll automatically. Displayed prices are reported feed values, not a promise of continuously updated pricing.

## Donations

Keep the current coming-soon area non-clickable until a verified public FuelLoc donation URL is available; do not ship a placeholder payment URL.

Once the public URL is available, open it outside the app workspace and check the complete donation flow on desktop before publishing.

## Explicitly deferred

Separate latitude/longitude input boxes, a new global custom context-menu system, and IP-based region inference are unnecessary for the first release. Visible location naming and remembered region selection cover the immediate workflows.
