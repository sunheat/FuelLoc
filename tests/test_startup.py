"""The local interface must start without importing the iPhone device stack."""

from pathlib import Path
import subprocess
import sys
import unittest


class StartupTests(unittest.TestCase):
    def test_local_interface_starts_before_device_imports(self):
        probe = '''
import importlib.abc
import runpy
import sys

class DeviceImportGuard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("pymobiledevice3"):
            raise AssertionError("Device stack imported before the local interface was ready")

sys.meta_path.insert(0, DeviceImportGuard())
namespace = runpy.run_path("src/main.py", run_name="startup_test")
with namespace["app"].test_client() as client:
    assert client.get("/").status_code == 200
'''
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=Path(__file__).parents[1], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_device_modules_do_not_need_the_interactive_shell(self):
        probe = '''
import importlib.abc
import sys

class ShellImportGuard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"IPython", "traitlets"}:
            raise ModuleNotFoundError(fullname)

sys.meta_path.insert(0, ShellImportGuard())
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
from pymobiledevice3.services.amfi import AmfiService
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
from pymobiledevice3.services.mobile_image_mounter import auto_mount
from pymobiledevice3.usbmux import list_devices
'''
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=Path(__file__).parents[1], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
