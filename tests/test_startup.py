"""The local interface must start without importing the iPhone device stack."""

from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch
import runpy


class StartupTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows work-area API")
    def test_window_size_respects_scaled_work_area_and_restores_dpi_context(self):
        namespace = runpy.run_path(str(Path(__file__).parents[1] / "src/main.py"), run_name="window_size_test")
        import ctypes

        for work_width, work_height, expected in [(1920, 1040, (1200, 780)), (1536, 832, (1200, 780)), (1280, 693, (1200, 661))]:
            with self.subTest(work_area=(work_width, work_height)):
                def query_area(action, unused, pointer, flags):
                    self.assertEqual(action, 48)
                    pointer._obj.right = work_width
                    pointer._obj.bottom = work_height
                    return True

                awareness = Mock(return_value=1234)
                with patch.object(ctypes.windll.user32, "SetThreadDpiAwarenessContext", awareness), patch.object(ctypes.windll.user32, "SystemParametersInfoW", query_area):
                    self.assertEqual(namespace["app_window_size"](), expected)
                    self.assertEqual([call.args for call in awareness.call_args_list], [(-1,), (1234,)])

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
