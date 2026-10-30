# Preferences and saved places

FuelLoc stores preferences and places in `%LOCALAPPDATA%/FuelLoc/state.sqlite3`. This is a local SQLite database using Python's standard library, independent of the browser's port or profile. Copy this file while FuelLoc is closed to back it up. Deleting it while the app is closed resets these features.

The app remembers dark/light mode, fuel mode, the chosen region, and the preferred fuel type. First launch uses dark mode, fuel enabled, and All Australia. If a preferred fuel type is unavailable in another region, the first available type is shown without discarding the preference. No IP lookup or location-permission prompt is added. A remembered region always comes from the user's choice.

**Saved places** opens the location list. **Save current location** stores the preview point with an optional name. Each row provides a preview button, a visible pencil button to name it, and a delete button. Names are plain text, limited to 80 characters. Named-place deletion asks for confirmation. Native dialogs support keyboard focus, Escape, and form submission; arrow keys in controls do not move the map pin.

A successful simulation automatically records the selected coordinates. Merely browsing fuel prices, searching, dragging a pin, and failed simulations do not add history. Revisiting identical coordinates moves them to the top and preserves their name. The latest 50 unnamed points are kept; named places remain until explicitly deleted. Selecting a saved place only previews it: the user must still click **Simulate Location**. Device connections and active simulations are never restored at startup.

Database writes are transactional. A failed preference or explicit save request shows an error; a history-write failure after a successful device action is logged without misreporting that action as failed. Local write endpoints retain the app's same-origin checks and validate preferences, names, and finite coordinate ranges.

Validation: run the Python unit suite and `tests/desktop_acceptance.py`. The browser check uses a temporary database and simulated phone responses, covering reload persistence, names containing HTML punctuation, renaming/deletion, preview-only selection, editing focus, and out-of-order fuel requests. No real phone or existing user data is changed.
