"""Persist preferences and location history independently of the browser origin."""

from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3


STATE_PATH = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "FuelLoc" / "state.sqlite3"
DEFAULTS = {"dark_mode": True, "fuel_enabled": True, "fuel_region": "All", "fuel_type": ""}
MAX_LOCATIONS = 30


def trim_location_history(connection):
    # Preserve named places, including collections created before the limit existed.
    connection.execute("""DELETE FROM locations WHERE name = '' AND id NOT IN
        (SELECT id FROM locations ORDER BY (name != '') DESC, id DESC LIMIT ?)""", (MAX_LOCATIONS,))


@contextmanager
def database():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(STATE_PATH, timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS preferences (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("""CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT, lat REAL NOT NULL, lng REAL NOT NULL,
                name TEXT NOT NULL DEFAULT '', UNIQUE(lat, lng))""")
            trim_location_history(connection)
            yield connection
    finally:
        connection.close()


def read_state():
    with database() as connection:
        preferences = dict(DEFAULTS)
        for row in connection.execute("SELECT key, value FROM preferences"):
            if row["key"] in preferences:
                preferences[row["key"]] = row["value"] == "true" if isinstance(DEFAULTS[row["key"]], bool) else row["value"]
        locations = [dict(row) for row in connection.execute("SELECT * FROM locations ORDER BY id DESC")]
    return {"preferences": preferences, "locations": locations}


def save_preferences(values):
    with database() as connection:
        for key, value in values.items():
            connection.execute("INSERT OR REPLACE INTO preferences VALUES (?, ?)",
                               (key, str(value).lower() if isinstance(value, bool) else value))


def save_location(lat, lng, name=None):
    with database() as connection:
        previous = connection.execute("SELECT name FROM locations WHERE lat = ? AND lng = ?", (lat, lng)).fetchone()
        if previous is None:
            total, unnamed = connection.execute("SELECT COUNT(*), COUNT(CASE WHEN name = '' THEN 1 END) FROM locations").fetchone()
            if total >= MAX_LOCATIONS and not unnamed:
                return False
        if name is None:
            name = previous["name"] if previous else ""
        # Revisit moves a point to the top, preserving its name.
        connection.execute("DELETE FROM locations WHERE lat = ? AND lng = ?", (lat, lng))
        connection.execute("INSERT INTO locations (lat, lng, name) VALUES (?, ?, ?)", (lat, lng, name))
        trim_location_history(connection)
    return True


def delete_location(location_id):
    with database() as connection:
        connection.execute("DELETE FROM locations WHERE id = ?", (location_id,))
