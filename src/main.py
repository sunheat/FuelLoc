"""FuelLoc's local device controller and map interface."""

import argparse
import asyncio
import json
import logging
import math
import os
import socket
import sys
import threading
import webbrowser
from urllib.request import urlopen

from flask import Flask, abort, jsonify, render_template, request
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.remote.userspace_tunnel import UserspaceRsdTunnel
from pymobiledevice3.services.amfi import AmfiService
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
from pymobiledevice3.services.mobile_image_mounter import auto_mount
from pymobiledevice3.usbmux import list_devices


logger = logging.getLogger("FuelLoc")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
app = Flask(__name__)
FUEL_API = "https://projectzerothree.info/api.php?format=json"
APP_VERSION = "0.1.0"
PORT = 54321
chosen_port = PORT
fuel_data = None
location = None


class AsyncRunner:
    """Keep the userspace tunnel and all device services on one event loop."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()

    def run(self, coroutine, timeout=40):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result(timeout)


class DeviceSession:
    def __init__(self):
        self.runner = AsyncRunner()
        self.tunnel = None
        self.rsd = None
        self.dvt = None
        self.simulation = None
        self.udid = None
        self.version = None

    async def close_location(self):
        if self.simulation is not None:
            try:
                await self.simulation.clear()
            finally:
                await self.simulation.close()
                self.simulation = None
        if self.dvt is not None:
            await self.dvt.close()
            self.dvt = None

    async def close(self):
        await self.close_location()
        if self.tunnel is not None:
            await self.tunnel.aclose()
            self.tunnel = None
            self.rsd = None
            self.udid = None
            self.version = None

    async def connect(self, udid, version):
        if self.udid == udid and self.rsd is not None:
            return self.rsd.service.address
        await self.close()
        lockdown = await create_using_usbmux(serial=udid, autopair=True)
        try:
            if not await lockdown.get_developer_mode_status():
                return None
        finally:
            await lockdown.close()
        tunnel = UserspaceRsdTunnel(serial=udid, autopair=True, remotepairing_fallback=True)
        try:
            rsd = await tunnel.aopen()
        except BaseException:
            await tunnel.aclose()
            raise
        self.tunnel = tunnel
        self.rsd = rsd
        self.udid = udid
        self.version = version
        return rsd.service.address

    async def set_location(self, latitude, longitude):
        if self.rsd is None:
            raise RuntimeError("Connect an iOS device first")
        if self.simulation is None:
            dvt = DvtProvider(self.rsd)
            await dvt.connect()
            try:
                simulation = LocationSimulation(dvt)
                await simulation.connect()
            except BaseException:
                await dvt.close()
                raise
            self.dvt = dvt
            self.simulation = simulation
        await self.simulation.set(latitude, longitude)

    async def enable_developer_mode(self, udid):
        lockdown = await create_using_usbmux(serial=udid, autopair=True)
        try:
            await AmfiService(lockdown).enable_developer_mode()
        finally:
            await lockdown.close()

    async def mount_image(self, udid):
        lockdown = await create_using_usbmux(serial=udid, autopair=True)
        try:
            await auto_mount(lockdown)
        finally:
            await lockdown.close()


session = DeviceSession()


@app.before_request
def local_requests_only():
    if request.host.split(":")[0] not in {"127.0.0.1", "localhost"}:
        abort(403)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("Origin")
        allowed = {f"http://127.0.0.1:{chosen_port}", f"http://localhost:{chosen_port}"}
        if origin and origin not in allowed:
            abort(403)
        if request.headers.get("Sec-Fetch-Site") == "cross-site":
            abort(403)


def get_fuel_data():
    global fuel_data
    if fuel_data is None:
        try:
            with urlopen(FUEL_API, timeout=10) as response:
                payload = response.read(2_000_001)
                if len(payload) > 2_000_000:
                    raise ValueError("Fuel-price response is too large")
                fuel_data = json.loads(payload)
        except Exception as error:
            logger.warning("Fuel prices unavailable: %s", error)
    return fuel_data


@app.get("/")
def index():
    return render_template(
        "map.html", user_locale="Australia", current_platform="Windows",
        app_version_num=APP_VERSION, app_version_type="fuel", sudo_message="",
        github_broadcast=None, version_message=None,
    )


@app.get("/api/fuel_types")
def fuel_types():
    data = get_fuel_data()
    if not data:
        return jsonify({"error": "Fuel prices unavailable"}), 503
    region = request.args.get("region", "All")
    prices = next((item.get("prices", []) for item in data.get("regions", []) if item.get("region") == region), [])
    return jsonify(sorted({item["type"] for item in prices if "type" in item}))


@app.get("/api/data/<fuel_type>")
def fuel_prices(fuel_type):
    data = get_fuel_data()
    if not data:
        return jsonify({"error": "Fuel prices unavailable"}), 503
    region = request.args.get("region", "All")
    prices = next((item.get("prices", []) for item in data.get("regions", []) if item.get("region") == region), [])
    return jsonify(next((item for item in prices if item.get("type") == fuel_type), None))


async def device_list():
    result = {}
    for device in await list_devices():
        udid = device.serial
        connection = device.connection_type
        try:
            lockdown = await create_using_usbmux(serial=udid, connection_type=connection, autopair=False)
            try:
                info = lockdown.short_info
            finally:
                await lockdown.close()
        except Exception as error:
            logger.warning("Device %s could not be inspected: %s", udid, error)
            info = {"Identifier": udid, "DeviceName": "iOS device", "DeviceClass": "Unknown", "ProductVersion": "Unknown"}
        info["ConnectionType"] = connection
        info["userLocale"] = "Australia"
        result.setdefault(udid, {}).setdefault(connection, []).append(info)
    return result


@app.get("/list_devices")
def list_connected_devices():
    try:
        return jsonify(session.runner.run(device_list()))
    except Exception as error:
        logger.warning("Device listing failed: %s", error)
        return jsonify({"error": str(error)}), 503


@app.post("/connect_device")
def connect_device():
    data = request.get_json(silent=True) or {}
    udid = data.get("udid")
    if not isinstance(udid, str) or not udid:
        return jsonify({"error": "Select a device"}), 400
    try:
        address = session.runner.run(session.connect(udid, data.get("ios_version")), timeout=90)
        if address is None:
            return jsonify({"developer_mode_required": True})
        return jsonify({"rsd_data": f"{address[0]}:{address[1]}"})
    except Exception as error:
        logger.warning("Device connection failed: %s", error)
        return jsonify({"error": str(error)}), 503


@app.post("/update_location")
def update_location():
    global location
    data = request.get_json(silent=True) or {}
    try:
        latitude, longitude = float(data["lat"]), float(data["lng"])
        if not math.isfinite(latitude) or not math.isfinite(longitude) or not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Coordinates outside valid range")
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid coordinates"}), 400
    location = latitude, longitude
    return "Location updated successfully"


@app.post("/set_location")
def set_location():
    if location is None:
        return jsonify({"error": "Select a location first"}), 400
    try:
        session.runner.run(session.set_location(*location))
        return "Location set successfully"
    except Exception as error:
        logger.warning("Setting location failed: %s", error)
        return jsonify({"error": str(error)}), 503


@app.post("/stop_location")
def stop_location():
    try:
        session.runner.run(session.close_location())
        return "Location cleared successfully"
    except Exception as error:
        return jsonify({"error": str(error)}), 503


@app.post("/stop_tunnel")
def stop_tunnel():
    try:
        session.runner.run(session.close())
        return jsonify("Tunnel stopped")
    except Exception as error:
        return jsonify({"error": str(error)}), 503


@app.post("/enable_developer_mode")
def enable_developer_mode():
    udid = (request.get_json(silent=True) or {}).get("udid")
    if not isinstance(udid, str) or not udid:
        return jsonify({"error": "Select a device"}), 400
    try:
        session.runner.run(session.enable_developer_mode(udid), timeout=180)
        return jsonify({"success": True, "udid": udid})
    except Exception as error:
        return jsonify({"error": str(error)}), 503


@app.post("/mount_developer_image")
def mount_developer_image():
    if not session.udid:
        return jsonify({"error": "Connect a device first"}), 400
    try:
        session.runner.run(session.mount_image(session.udid), timeout=180)
        return "Developer image mounted successfully"
    except Exception as error:
        return jsonify({"error": str(error)}), 503


@app.post("/exit")
def exit_app():
    try:
        session.runner.run(session.close())
    finally:
        threading.Timer(0.2, lambda: os._exit(0)).start()
    return jsonify({"success": True})


def select_port(requested):
    if requested:
        return requested
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", PORT))
            return PORT
        except OSError:
            probe.bind(("127.0.0.1", 0))
            return probe.getsockname()[1]


def main():
    global chosen_port
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    chosen_port = select_port(args.port)
    url = f"http://127.0.0.1:{chosen_port}"
    logger.info("Opening %s", url)
    if not args.no_browser:
        threading.Timer(1, lambda: webbrowser.open(url)).start()
    app.run(debug=False, use_reloader=False, host="127.0.0.1", port=chosen_port)


if __name__ == "__main__":
    main()
