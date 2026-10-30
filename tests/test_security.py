import runpy
import sys
from unittest.mock import patch
import unittest
from pathlib import Path


class SecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(sys, "argv", ["main.py"]):
            cls.namespace = runpy.run_path(str(Path(__file__).parents[1] / "src" / "main.py"), run_name="fuel_loc_test")
        cls.namespace["app"].testing = True
        cls.namespace["app"].config["SERVER_NAME"] = "127.0.0.1:54321"
        cls.namespace["local_requests_only"].__globals__["chosen_port"] = 54321

    def test_cross_origin_write_is_rejected(self):
        with self.namespace["app"].test_client() as client:
            response = client.post("/update_location", json={"lat": -33.86, "lng": 151.21}, headers={"Origin": "https://attacker.example"})
            self.assertEqual(response.status_code, 403)

    def test_same_origin_write_is_allowed(self):
        with self.namespace["app"].test_client() as client:
            response = client.post("/update_location", json={"lat": -33.86, "lng": 151.21}, headers={"Origin": "http://127.0.0.1:54321"})
            self.assertEqual(response.status_code, 200)


    def test_invalid_coordinates_are_rejected(self):
        with self.namespace["app"].test_client() as client:
            response = client.post("/update_location", json={"lat": 999, "lng": 151.21}, headers={"Origin": "http://127.0.0.1:54321"})
            self.assertEqual(response.status_code, 400)

    def test_userspace_tunnel_connects_without_driver_setup(self):
        namespace = self.namespace
        fake_rsd = type("Rsd", (), {"service": type("Service", (), {"address": ("fd00::1", 1234)})()})()
        class FakeLockdown:
            async def get_developer_mode_status(self):
                return True
            async def close(self):
                return None
        class FakeTunnel:
            def __init__(self, **kwargs):
                self.kwargs = kwargs
            async def aopen(self):
                return fake_rsd
            async def aclose(self):
                return None
        async def fake_lockdown(**kwargs):
            return FakeLockdown()
        session = namespace["DeviceSession"]()
        with patch("pymobiledevice3.lockdown.create_using_usbmux", fake_lockdown), patch("pymobiledevice3.remote.userspace_tunnel.UserspaceRsdTunnel", FakeTunnel):
            self.assertEqual(session.runner.run(session.connect("TEST-UDID", "18.0")), ("fd00::1", 1234))
            self.assertIs(session.rsd, fake_rsd)
            session.runner.run(session.close())

if __name__ == "__main__":
    unittest.main()
