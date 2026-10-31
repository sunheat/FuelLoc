# First release checklist

## Interaction and local data

- Start from the intended merged source revision. Keep address and coordinate search in one field for this release.
- Run the Python unit suite, all three Node checks, and Edge desktop acceptance as described in [BUILDING.md](BUILDING.md). Check normal wheel, Ctrl + wheel, keyboard zoom, context menus, and keyboard editing.
- Verify Windows display scaling at 125% and 150% on a real desktop. Automated viewport checks exercise available layout space; they do not replace a native DPI check.
- Keep the first region as All Australia, then remember user selection. IP-based defaults are deferred; no new lookup service or location permission is needed.

## Distribution

- Run `scripts/package.ps1` from a clean, committed checkout. Check the EXE's product/file version against `APP_VERSION`, and verify the recorded source commit and archive checksums.
- Extract the portable ZIP to a fresh folder and test it on a Windows account without the development environment. Keep this separate from a smoke check on the development machine.
- Check EXE, setup window, workspace header, and browser app-window icons. Browser taskbar grouping remains browser-owned.
- Test missing Apple device support, no phone, no Internet, a busy local port, and closing/reopening the app. Keep setup errors readable and entry available when the local app is ready.
- Before publishing, perform a short real-device connect, simulate, stop, disconnect, and exit check. Automated acceptance uses mocks and does not exercise a physical phone.
- Prepare a matching source archive and retain LICENSE, dependency notices, and upstream attribution. Confirm the archive includes the entire `_internal` folder and no local configuration, credentials, or saved-location data.
- Verify the live feed's available regions, timestamps, and freshness after leaving the app open. The cache refreshes on the next fuel request after five minutes; the displayed price does not poll automatically. Displayed prices are reported feed values, not a promise of continuously updated pricing.
- Check README links, the workspace screenshot, GitHub homepage, Issues entry, and `.github/FUNDING.yml`. Describe Windows x64 as the only binary target and disclose the unsigned EXE and limited device verification.

## Donations

The app links to the owner's supplied public page at `https://ko-fi.com/sunheat` from the footer and successful simulation dialog. Before publishing, open both links outside the app workspace and check the donation flow on desktop. The local app must never load payment scripts or handle payment details.

## Publication approval

- Present the proposed tag `v1.0.0`, title `FuelLoc 1.0.0`, source commit, [release notes](releases/1.0.0.md), exact download files, checksums, and any uncompleted manual checks to the owner.
- Stop and wait for an explicit follow-up confirming publication. Building archives or committing preparation changes is not permission to publish a release.
- After approval, merge the preparation changes, ensure the release source matches the tested build, and create the tag at that source revision. If source changes, rebuild and recheck the archives first.
- Create the GitHub Release with the portable ZIP, matching source ZIP, and `SHA256SUMS.txt`. Check the public downloads and their hashes after publication. Never upload the standalone intermediate EXE or the local review notes.

## Explicitly deferred

Separate latitude/longitude input boxes, a new global custom context-menu system, and IP-based region inference are unnecessary for the first release. Visible location naming and remembered region selection cover the immediate workflows.
