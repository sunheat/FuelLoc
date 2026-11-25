"""Exercise location replacement through HTTP with the reported sticky device behavior."""

from pathlib import Path
import asyncio
import runpy
import sys
import unittest
from unittest.mock import patch
from unittest.mock import AsyncMock
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class LocationSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = runpy.run_path(
            str(Path(__file__).parents[1] / "src/main.py"), run_name="location_session_test",
        )
        cls.namespace["app"].testing = True

    def setUp(self):
        self.position = None
        self.clear_error = None
        self.set_error = None
        self.events = []
        test = self

        class FakeDvt:
            def __init__(self, rsd):
                pass

            async def connect(self):
                await asyncio.sleep(0)

            async def close(self):
                test.events.append("close")

        class StickySimulation:
            """Model the report: a new override is ignored until restoration."""

            def __init__(self, dvt):
                pass

            async def connect(self):
                pass

            async def set(self, latitude, longitude):
                if test.set_error:
                    raise test.set_error
                test.events.append("set")
                if test.position is None:
                    test.position = latitude, longitude

            async def clear(self):
                await asyncio.sleep(0)  # Device I/O lets other requests run.
                if test.clear_error:
                    raise test.clear_error
                test.events.append("clear")
                test.position = None

            async def close(self):
                pass

        self.session = self.namespace["session"]
        self.session.rsd = object()
        self.session.tunnel = SimpleNamespace(rsd=self.session.rsd, aclose=AsyncMock())
        self.session.simulation = None
        self.session.dvt = None
        for target, replacement in [
            ("pymobiledevice3.services.dvt.instruments.dvt_provider.DvtProvider", FakeDvt),
            ("pymobiledevice3.services.dvt.instruments.location_simulation.LocationSimulation", StickySimulation),
        ]:
            patcher = patch(target, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)
        history_patcher = patch("user_state.save_location")
        self.history = history_patcher.start()
        self.addCleanup(history_patcher.stop)
        self.client = self.namespace["app"].test_client()

    def select(self, point):
        response = self.client.post("/update_location", json=dict(zip(("lat", "lng"), point)))
        self.assertEqual(response.status_code, 200)

    def test_repeated_set_replaces_position_without_a_manual_stop(self):
        rsd = self.session.rsd
        for point in [(-33.86, 151.21), (-37.81, 144.96), (-27.47, 153.03)]:
            self.select(point)
            response = self.client.post("/set_location")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, "Location set successfully")
            self.assertEqual(self.position, point, "A successful replacement must apply the new position")
        self.assertIs(self.session.rsd, rsd, "Location replacement must preserve the device tunnel")
        self.assertEqual(self.history.call_count, 3)

        response = self.client.post("/stop_location")
        self.assertEqual(response.text, "Location cleared successfully")
        self.assertIsNone(self.position)
        self.assertIsNone(self.session.simulation)
        self.assertIsNone(self.session.dvt)
        self.events.clear()
        self.assertEqual(self.client.post("/set_location").status_code, 200)
        self.assertEqual(self.position, point)
        self.assertEqual(self.events, ["set"], "A fresh session needs no restoration")

    def test_replacement_failure_does_not_report_or_save_success(self):
        self.select((-33.86, 151.21))
        self.assertEqual(self.client.post("/set_location").status_code, 200)
        self.select((-37.81, 144.96))
        for stage in ("clear", "set"):
            with self.subTest(stage=stage):
                self.history.reset_mock()
                self.session.rsd = object()
                self.session.tunnel = SimpleNamespace(rsd=self.session.rsd, aclose=AsyncMock())
                if stage == "set":
                    self.session.runner.run(self.session.set_location(-33.86, 151.21))
                    self.history.reset_mock()
                setattr(self, stage + "_error", RuntimeError(stage + " failed"))
                try:
                    response = self.client.post("/set_location")
                    self.assertEqual(response.status_code, 503)
                    self.assertEqual(response.json, {"error": stage + " failed"})
                    self.history.assert_not_called()
                finally:
                    setattr(self, stage + "_error", None)

    def test_overlapping_replacements_and_stop_finish_in_order(self):
        self.session.runner.run(self.session.set_location(-33.86, 151.21))

        async def replace_and_stop():
            await asyncio.gather(
                self.session.set_location(-37.81, 144.96),
                self.session.set_location(-27.47, 153.03),
                self.session.close_location(),
            )

        self.session.runner.run(replace_and_stop())
        self.assertIsNone(self.position, "The final stop must restore the real location")
        self.assertIsNone(self.session.simulation)
        self.assertIsNone(self.session.dvt)


if __name__ == "__main__":
    unittest.main()
