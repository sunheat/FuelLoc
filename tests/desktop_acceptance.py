"""Desktop layout and interaction checks with a simulated phone.

Run: .venv/Scripts/python tests/desktop_acceptance.py
Requires the development-only playwright package and Microsoft Edge.
No requests reach a real phone. External map libraries use their pinned URLs.
"""

import json
from pathlib import Path
import runpy
import threading

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server


ROOT = Path(__file__).resolve().parents[1]


def assert_fits(page, selectors):
    overflow = page.evaluate("""() => ({
        x: document.documentElement.scrollWidth - innerWidth,
        y: document.documentElement.scrollHeight - innerHeight
    })""")
    assert overflow == {"x": 0, "y": 0}, f"Page requires scrolling: {overflow}"
    if page.locator('.sidebar-content').count():
        assert page.locator('.sidebar-content').evaluate("e => e.scrollHeight <= e.clientHeight + 1"), "Sidebar requires scrolling"
    for selector in selectors:
        box = page.locator(selector).bounding_box()
        size = page.viewport_size
        assert box and box["x"] >= 0 and box["y"] >= 0, selector
        assert box["x"] + box["width"] <= size["width"] + 1, selector
        assert box["y"] + box["height"] <= size["height"] + 1, selector


def main():
    (ROOT / "build").mkdir(exist_ok=True)
    namespace = runpy.run_path(str(ROOT / "src/main.py"), run_name="desktop_test")
    server = make_server("127.0.0.1", 0, namespace["app"], threaded=True)
    namespace["local_requests_only"].__globals__["chosen_port"] = server.server_port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    calls = []
    phone = {"Identifier": "test-phone", "ConnectionType": "USB", "DeviceName": "Test iPhone",
             "DeviceClass": "iPhone", "ProductVersion": "18.7", "userLocale": "Australia"}

    def api(route):
        path = route.request.url.split(url)[1].split("?")[0]
        calls.append((path, route.request.post_data))
        responses = {
            "/list_devices": {"test-phone": {"USB": [phone]}},
            "/connect_device": {"rsd_data": "test-session"},
            "/api/fuel_types": ["U91", "U95"],
            "/api/data/U91": {"type": "U91", "price": 170.9, "suburb": "Sydney", "state": "NSW", "lat": -33.86, "lng": 151.21},
            "/api/data/U95": {"type": "U95", "price": 180.9, "suburb": "Melbourne", "state": "VIC", "lat": -37.81, "lng": 144.96},
        }
        route.fulfill(status=200, content_type="application/json", body=json.dumps(responses.get(path, "OK")))

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width": 1200, "height": 720})
            page.route(url + "/**", lambda route: route.continue_() if route.request.url == url + "/" or route.request.url.startswith(url + '/static/') else api(route))
            page.route("https://nominatim.openstreetmap.org/**", lambda route: route.fulfill(
                content_type="application/json", body=json.dumps([{"lat": "-33.86", "lon": "151.21", "display_name": "Sydney", "boundingbox": ["-34", "-33", "151", "152"]}])))
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(url, wait_until="networkidle")
            page.wait_for_function("typeof map !== 'undefined' && map && map._loaded")
            assert page.locator('.brand-icon').evaluate('e => e.complete && e.naturalWidth === 256')
            assert page.request.get(url + '/static/fuelloc.ico').status == 200
            controls = ["#device", "#refresh", "#connect", "#coordinates", "#search", "#set-location", "#stop-location", "#map"]
            page.screenshot(path=str(ROOT / "build/desktop-dark.png"))
            assert_fits(page, controls)
            assert page.locator('#enableFuelPrices').is_checked()
            page.wait_for_function("document.getElementById('fuelText').value.includes('Sydney')")
            controls += ['#fuelRegion', '#fuelType', '#fuelText']
            for width, height in [(1200, 740), (1200, 620), (1200, 600), (960, 600), (1536, 800), (1920, 980)]:
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_timeout(200)
                assert_fits(page, controls)
                assert page.evaluate("Math.abs(map.getSize().x - document.getElementById('map').clientWidth) < 2")
                print(f"PASS: {width}x{height}, fuel details and primary controls fully visible")

            page.set_viewport_size({"width": 1200, "height": 720})
            page.locator('#map').hover()
            zoom = page.evaluate('map.getZoom()')
            page.mouse.wheel(0, -300)
            page.wait_for_timeout(300)
            assert page.evaluate('map.getZoom()') == zoom, 'Ordinary scrolling zoomed the map'
            assert page.locator('#mapWheelHint').is_visible(), 'Scrolling needs an on-map Ctrl hint'
            page.keyboard.down('Control')
            assert not page.locator('#mapWheelHint').is_visible(), 'Ctrl should immediately dismiss the hint'
            page.keyboard.up('Control')
            page.keyboard.down('Control')
            page.mouse.wheel(0, -300)
            page.keyboard.up('Control')
            page.wait_for_timeout(600)
            assert page.evaluate('map.getZoom()') > zoom, 'Ctrl + wheel did not zoom'
            zoom = page.evaluate('map.getZoom()')
            page.mouse.wheel(0, 300)
            page.wait_for_timeout(300)
            assert page.evaluate('map.getZoom()') == zoom, 'Ordinary scrolling after Ctrl zoom changed the map'
            print('PASS: wheel gestures only zoom with Ctrl')

            assert page.evaluate("""() => !document.querySelector('.app-header').dispatchEvent(
                new WheelEvent('wheel', {ctrlKey: true, deltaY: -100, bubbles: true, cancelable: true}))"""), 'Page zoom gesture was not cancelled outside the map'
            assert page.evaluate("""() => !document.dispatchEvent(new KeyboardEvent('keydown', {
                key: '+', ctrlKey: true, bubbles: true, cancelable: true}))"""), 'Keyboard page zoom was not cancelled'
            assert page.locator('.app-header').evaluate("e => !e.dispatchEvent(new MouseEvent('contextmenu', {bubbles: true, cancelable: true}))")
            assert page.locator('#coordinates').evaluate("e => e.dispatchEvent(new MouseEvent('contextmenu', {bubbles: true, cancelable: true}))"), 'Text editing menu must remain available'
            print('PASS: page zoom suppressed and text context menu preserved')

            page.locator('#map').dblclick(position={"x": 300, "y": 200})
            page.wait_for_timeout(200)
            assert page.locator('#coordinates').input_value()
            assert page.locator('#set-location').is_disabled()
            page.locator('#connect').click()
            page.wait_for_function("document.getElementById('connectText').textContent === 'Connected'")
            assert page.locator('#set-location').is_enabled()
            assert page.locator('#stop-location').is_enabled()
            assert_fits(page, controls + ['#disconnect'])
            page.locator('#set-location').click()
            page.locator('#stop-location').click()
            page.locator('#disconnect').click()
            assert page.locator('#set-location').is_disabled()
            assert page.locator('#stop-location').is_disabled()
            for endpoint in ['/connect_device', '/update_location', '/set_location', '/stop_location']:
                assert any(path == endpoint for path, _ in calls), endpoint
            print('PASS: connection, map selection, location set, stop, and disconnect')

            page.locator('#fuelType').select_option('U95')
            page.wait_for_function("document.getElementById('fuelText').value.includes('Melbourne')")
            assert page.locator('#coordinates').input_value() == '-37.81, 144.96'
            page.locator('#fuelRegion').select_option('VIC')
            page.wait_for_timeout(200)
            page.locator('#enableFuelPrices').uncheck()
            assert not page.locator('#fuelText').is_visible()
            page.locator('#enableFuelPrices').check()
            page.wait_for_function("document.getElementById('fuelText').value.includes('Melbourne')")
            assert page.locator('#set-location').is_disabled(), 'Fuel selection re-enabled location after disconnect'
            assert page.locator('#stop-location').is_disabled()
            assert_fits(page, controls)
            print('PASS: fuel defaults, region/type selection and mode toggle')

            page.locator('#mapTools').click()
            assert page.locator('div.leaflet-control-filelayer').is_visible()
            page.locator('#mapTools').click()
            assert not page.locator('div.leaflet-control-filelayer').is_visible()
            page.locator('#darkModeSwitch').uncheck()
            assert not page.locator('body').evaluate("e => e.classList.contains('dark-mode')")
            page.wait_for_timeout(250)
            page.screenshot(path=str(ROOT / 'build/desktop-light.png'))
            page.locator('#darkModeSwitch').check()
            page.wait_for_timeout(250)
            page.locator('.toast.show').evaluate_all("elements => elements.forEach(e => bootstrap.Toast.getOrCreateInstance(e).hide())")
            page.wait_for_timeout(200)
            page.screenshot(path=str(ROOT / 'build/desktop-dark.png'))
            page.route(url + '/list_devices', lambda route: route.fulfill(content_type='application/json', body='{}'))
            page.locator('#refresh').click()
            page.wait_for_function("document.getElementById('device').textContent.includes('No device found')")
            page.route(url + '/api/fuel_types**', lambda route: route.fulfill(status=503, content_type='application/json', body='{}'))
            page.locator('#fuelRegion').select_option('NSW')
            page.wait_for_function("document.getElementById('fuelStatus').textContent.includes('unavailable')")
            assert not page.locator('#fuelText').is_visible()
            assert_fits(page, [c for c in controls if c != '#fuelText'])
            print('PASS: missing phone and unavailable fuel feed remain usable')
            assert not errors, errors
            print("PASS: default desktop layout fits without page scrolling")
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
