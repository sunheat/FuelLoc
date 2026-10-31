"""Fuel feed cache expiry must trigger a new download, without stale fallback."""

from io import BytesIO
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))


class FuelCacheTests(unittest.TestCase):
    def setUp(self):
        namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'src/main.py'), run_name='fuel_cache_test')
        self.get_data = namespace['get_fuel_data']
        self.now = 100
        self.downloads = 0

        def download(*args, **kwargs):
            self.downloads += 1
            return BytesIO(json.dumps({'regions': [], 'download': self.downloads}).encode())

        self.clock_patch = patch.dict(self.get_data.__globals__, {
            'urlopen': download, 'time': SimpleNamespace(monotonic=lambda: self.now),
        })
        self.clock_patch.start()
        self.addCleanup(self.clock_patch.stop)

    def test_cache_reuses_fresh_data_and_refreshes_after_five_minutes(self):
        self.assertEqual(self.get_data()['download'], 1)
        self.now += 299
        self.assertEqual(self.get_data()['download'], 1)
        self.now += 2
        self.assertEqual(self.get_data()['download'], 2)
        self.assertEqual(self.downloads, 2)

    def test_expired_data_is_not_returned_if_refresh_fails(self):
        self.get_data()
        self.now += 301
        with patch.dict(self.get_data.__globals__, {'urlopen': Mock(side_effect=OSError('Offline'))}):
            self.assertIsNone(self.get_data())
        self.assertEqual(self.get_data()['download'], 2)
