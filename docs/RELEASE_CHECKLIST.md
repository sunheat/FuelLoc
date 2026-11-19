# Release checklist

## Preparation

- Confirm the release contains the intended fixes and their regression coverage.
- Match `APP_VERSION`, Windows file/product metadata, portable instructions, release notes, and archive filenames.
- Describe user-visible changes, upgrade steps, supported platforms, and known limitations. Keep local investigation logs and device records out of public artifacts.
- Retain the GPLv3 license, upstream attribution, dependency notices, and map attribution.

## Validation

- Use the checks in [BUILDING.md](BUILDING.md) for affected behavior. Record results locally rather than embedding session transcripts in release notes.
- For device changes, verify connection, consecutive location changes, restoration, disconnect, and exit on a physical iPhone. Confirm the phone's displayed location.
- Check the portable distribution, startup prerequisites, and local data preservation. Missing Apple support, a disconnected phone, or unavailable Internet should produce useful guidance.

## Packaging

- Commit the intended source and run `scripts/package.ps1` from a clean checkout.
- Check the executable version and the source commit in `BUILD-INFO.txt`.
- Confirm the portable ZIP contains the complete `FuelLoc/` folder and `_internal` runtime, licenses, user instructions, release notes, and dependency information.
- Confirm the source ZIP matches the release commit and excludes local configuration, credentials, user data, and build outputs.
- Verify both archive hashes against `SHA256SUMS.txt`.

## Publication

- Tag the packaged source revision without moving an existing tag. FuelLoc 1.0.1 uses `fuelloc-v1.0.1` because `v1.0.1` belongs to inherited upstream history.
- Publish a GitHub Release with the Windows portable ZIP, matching source ZIP, and checksum file.
- Set the current stable release as latest and confirm the public asset names, sizes, and hashes.
- Retain earlier releases for reference and link superseded releases to the current version when appropriate.
