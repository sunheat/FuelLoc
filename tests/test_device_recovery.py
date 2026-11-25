"""Reproduce cable loss at the device-session boundary without touching hardware."""

import asyncio
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


class DeviceRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.namespace = runpy.run_path(str(Path(__file__).parents[1] / "src/main.py"))

    def setUp(self):
        self.session = self.namespace["DeviceSession"]()
        self.rsd = SimpleNamespace(service=SimpleNamespace(address=("fd00::1", 1234)))
        self.old_tunnel = SimpleNamespace(rsd=None, aclose=AsyncMock())
        self.session.tunnel = self.old_tunnel
        self.session.rsd = self.rsd
        self.session.udid = "test-device"
        self.session.version = "18.0"
        self.simulation = SimpleNamespace(
            clear=AsyncMock(side_effect=RuntimeError("userspace dial plane is closed")),
            close=AsyncMock(),
        )
        self.dvt = SimpleNamespace(close=AsyncMock())
        self.session.simulation = self.simulation
        self.session.dvt = self.dvt
        self.addCleanup(self.stop_runner)

    def stop_runner(self):
        self.session.runner.loop.call_soon_threadsafe(self.session.runner.loop.stop)
        self.session.runner.thread.join(timeout=2)
        self.session.runner.loop.close()

    def test_disconnect_releases_every_resource_even_when_restoration_fails(self):
        try:
            self.session.runner.run(self.session.close())
        except RuntimeError:
            pass
        self.assertIsNone(self.session.simulation)
        self.assertIsNone(self.session.dvt)
        self.assertIsNone(self.session.rsd)
        self.assertIsNone(self.session.udid)
        self.simulation.close.assert_awaited_once()
        self.dvt.close.assert_awaited_once()
        self.old_tunnel.aclose.assert_awaited_once()

    def test_reconnect_same_phone_replaces_transport_closed_by_library(self):
        fresh_rsd = SimpleNamespace(service=SimpleNamespace(address=("fd00::2", 5678)))
        fresh_tunnel = SimpleNamespace(aopen=AsyncMock(return_value=fresh_rsd), aclose=AsyncMock())
        lockdown = SimpleNamespace(get_developer_mode_status=AsyncMock(return_value=True), close=AsyncMock())
        with patch("pymobiledevice3.lockdown.create_using_usbmux", AsyncMock(return_value=lockdown)), patch(
            "pymobiledevice3.remote.userspace_tunnel.UserspaceRsdTunnel", return_value=fresh_tunnel,
        ) as factory:
            address = self.session.runner.run(self.session.connect("test-device", "18.0"))
        self.assertEqual(address, ("fd00::2", 5678), "Reconnect must not return the cached dead RSD")
        factory.assert_called_once()

    def test_status_invalidates_a_dead_tunnel_even_after_phone_is_replugged(self):
        async def devices():
            return {"test-device": {"USB": []}}

        with patch.dict(self.session.status.__globals__, device_list=devices):
            status = self.session.runner.run(self.session.status())
        self.assertEqual(status["rsd_data"], "")
        self.assertIsNone(status["udid"])
        self.assertIn("test-device", status["devices"])
        self.simulation.clear.assert_not_awaited()
        self.old_tunnel.aclose.assert_awaited_once()

    def test_status_invalidates_a_phone_missing_from_usbmux(self):
        self.old_tunnel.rsd = self.rsd
        with patch.dict(self.session.status.__globals__, device_list=AsyncMock(return_value={})):
            status = self.session.runner.run(self.session.status())
        self.assertEqual(status, {"devices": {}, "udid": None, "rsd_data": ""})
        self.simulation.clear.assert_not_awaited()

    def test_cleanup_continues_after_a_service_close_error(self):
        self.simulation.close.side_effect = OSError("USB disconnected")
        with self.assertRaisesRegex(RuntimeError, "userspace dial plane is closed"):
            self.session.runner.run(self.session.close())
        self.assertIsNone(self.session.tunnel)
        self.assertIsNone(self.session.simulation)
        self.dvt.close.assert_awaited_once()
        self.old_tunnel.aclose.assert_awaited_once()

    def test_stop_after_disconnect_cannot_report_restoration_success(self):
        with self.assertRaisesRegex(RuntimeError, "Reconnect before restoring"):
            self.session.runner.run(self.session.close_location())
        self.assertIsNone(self.session.rsd)
        self.simulation.clear.assert_not_awaited()

    def test_request_timeout_cancels_device_work_and_releases_resources(self):
        self.old_tunnel.rsd = self.rsd
        self.simulation.clear.side_effect = lambda: None

        async def stalled_clear():
            await asyncio.Event().wait()

        self.simulation.clear.side_effect = stalled_clear
        with self.assertRaises(TimeoutError):
            self.session.runner.run(self.session.close_location(), timeout=0.02)
        self.assertIsNone(self.session.rsd)
        self.dvt.close.assert_awaited_once()
        self.old_tunnel.aclose.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
