"""Local persistence, HTTP validation, and successful-simulation history."""

from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import user_state


class UserStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path_patch = patch.object(user_state, 'STATE_PATH', Path(self.directory.name) / 'state.sqlite3')
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)
        self.namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'src/main.py'), run_name='state_test')
        self.client = self.namespace['app'].test_client()

    def test_preferences_and_locations_persist_across_connections(self):
        self.assertEqual(self.client.put('/api/preferences', json={'dark_mode': False, 'fuel_region': 'VIC', 'fuel_type': 'U95', 'fuel_enabled': False}).status_code, 200)
        self.assertEqual(self.client.post('/api/locations', json={'lat': -37.81, 'lng': 144.96, 'name': '<Home>'}).status_code, 200)
        state = user_state.read_state()
        self.assertFalse(state['preferences']['dark_mode'])
        self.assertEqual(state['preferences']['fuel_type'], 'U95')
        self.assertEqual(state['locations'][0]['name'], '<Home>')
        user_state.save_location(-37.81, 144.96)
        self.assertEqual(len(user_state.read_state()['locations']), 1)
        self.assertEqual(user_state.read_state()['locations'][0]['name'], '<Home>')
        self.client.delete(f"/api/locations/{user_state.read_state()['locations'][0]['id']}")
        self.assertEqual(user_state.read_state()['locations'], [])

    def test_named_places_survive_history_limit(self):
        user_state.save_location(-37, 144, 'Keep me')
        for offset in range(60):
            user_state.save_location(offset, 10)
        places = user_state.read_state()['locations']
        self.assertEqual(len(places), 51)
        self.assertEqual(places[-1]['name'], 'Keep me')

    def test_invalid_and_cross_origin_writes_are_rejected(self):
        for payload in [{'dark_mode': 'false'}, {'fuel_region': []}, {'unknown': 1}, []]:
            self.assertEqual(self.client.put('/api/preferences', json=payload).status_code, 400)
        for payload in [{'lat': 999, 'lng': 1}, {'lat': 1, 'lng': 2, 'name': 'x' * 81}, None]:
            self.assertEqual(self.client.post('/api/locations', json=payload).status_code, 400)
        for method, url, payload in [('put', '/api/preferences', {'dark_mode': False}), ('post', '/api/locations', {'lat': 1, 'lng': 2}), ('delete', '/api/locations/1', None)]:
            self.assertEqual(getattr(self.client, method)(url, json=payload, headers={'Origin': 'https://example.com'}).status_code, 403)

    def test_only_successful_simulation_records_history(self):
        self.client.post('/update_location', json={'lat': -33.86, 'lng': 151.21})
        self.assertEqual(user_state.read_state()['locations'], [])
        function_globals = self.namespace['set_location'].__globals__
        runner = SimpleNamespace(run=lambda value: value)
        session = SimpleNamespace(runner=runner, set_location=lambda *args: None)
        with patch.dict(function_globals, {'session': session}):
            self.assertEqual(self.client.post('/set_location').status_code, 200)
        self.assertEqual(user_state.read_state()['locations'][0]['lat'], -33.86)
        user_state.delete_location(user_state.read_state()['locations'][0]['id'])
        def fail(*args):
            raise RuntimeError('Disconnected')
        session.set_location = fail
        with patch.dict(function_globals, {'session': session}):
            self.assertEqual(self.client.post('/set_location').status_code, 503)
        self.assertEqual(user_state.read_state()['locations'], [])
