"""Desktop layout and interaction checks with a simulated phone.

Run: .venv/Scripts/python tests/desktop_acceptance.py
Requires the development-only playwright package and Microsoft Edge.
No requests reach a real phone. External map libraries use their pinned URLs.
"""

import json
from pathlib import Path
import runpy
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


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
    state_directory = tempfile.TemporaryDirectory()
    namespace['user_state'].STATE_PATH = Path(state_directory.name) / 'state.sqlite3'
    server = make_server("127.0.0.1", 0, namespace["app"], threaded=True)
    namespace["local_requests_only"].__globals__["chosen_port"] = server.server_port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    calls = []
    phone_connected = False
    phone = {"Identifier": "test-phone", "ConnectionType": "USB", "DeviceName": "Test iPhone",
             "DeviceClass": "iPhone", "ProductVersion": "18.7", "userLocale": "Australia"}

    def api(route):
        path = route.request.url.split(url)[1].split("?")[0]
        if path.startswith(('/api/user_state', '/api/preferences', '/api/locations')):
            route.continue_()
            return
        calls.append((path, route.request.post_data))
        responses = {
            "/list_devices": {"test-phone": {"USB": [phone]}} if phone_connected else {},
            "/connect_device": {"rsd_data": "test-session"},
            "/api/fuel_types": ["U91", "U95"],
            "/api/data/U91": {"type": "U91", "price": 170.9, "suburb": "Sydney", "state": "NSW", "lat": -33.86, "lng": 151.21},
            "/api/data/U95": {"type": "U95", "price": 180.9, "suburb": "Melbourne", "state": "VIC", "lat": -37.81, "lng": 144.96},
        }
        if path in {'/set_location', '/stop_location'}:
            route.fulfill(content_type='text/plain', body='Location set successfully' if path == '/set_location' else 'Location cleared successfully')
            return
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
            controls = ["#device", "#refresh", "#connect", "#coordinates", "#search", "#savedPlaces", "#set-location", "#stop-location", "#map"]
            assert page.locator('.map-search #savedPlaces').count() == 1
            assert page.locator('.app-header #savedPlaces').count() == 0
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
            page.wait_for_function("document.getElementById('device').textContent.includes('No device found')")
            phone_connected = True
            page.locator('#refresh').click()
            page.wait_for_function("document.getElementById('device').textContent.includes('Test iPhone')")
            page.locator('#connect').click()
            page.wait_for_function("document.getElementById('connectText').textContent === 'Connected'")
            page.locator('#workspaceNotification').wait_for(state='visible')
            assert page.locator('#workspaceNotification').inner_text() == 'Device connected'
            assert not page.locator('#locationResultDialog').is_visible()
            assert page.locator('#device').is_disabled()
            assert page.locator('#device').evaluate("e => e.selectedOptions[0].textContent.includes('Test iPhone')")
            assert page.locator('#device').evaluate("e => getComputedStyle(e).backgroundColor === getComputedStyle(document.getElementById('fuelRegion')).backgroundColor"), 'Disabled device selector must retain the themed background so its label stays readable'
            page.locator('#darkModeSwitch').uncheck()
            assert page.locator('#device').evaluate("e => getComputedStyle(e).backgroundColor === getComputedStyle(document.getElementById('fuelRegion')).backgroundColor"), 'Disabled device selector must match the light theme too'
            page.screenshot(path=str(ROOT / 'build/device-connected-light.png'))
            page.locator('#darkModeSwitch').check()
            page.screenshot(path=str(ROOT / 'build/device-connected-dark.png'))
            assert page.locator('#set-location').is_enabled()
            assert page.locator('#stop-location').is_enabled()
            assert_fits(page, controls + ['#disconnect'])
            page.locator('#set-location').click()
            result = page.locator('#locationResultDialog')
            result.wait_for(state='visible')
            assert result.evaluate("e => e.matches(':modal')"), 'Result must block the workspace'
            assert page.locator('#locationResultHeading').inner_text() == 'Location set'
            assert page.locator('#locationResultMessage').is_visible()
            assert page.locator('#locationResultMessage').inner_text() == 'Enjoy! Use Stop Location to restore your real location.'
            assert page.locator('#locationResultMessage').evaluate("e => parseFloat(getComputedStyle(e).fontSize) < parseFloat(getComputedStyle(document.getElementById('locationResultHeading')).fontSize)")
            assert result.evaluate("e => getComputedStyle(e, '::backdrop').backgroundColor === getComputedStyle(document.getElementById('savedPlacesDialog'), '::backdrop').backgroundColor")
            assert page.locator('#locationResultSupport').is_visible()
            assert page.evaluate('locationResultAnimation.effect.getTiming().duration') == 6000
            assert page.locator('#locationResultOK').evaluate('e => e === document.activeElement')
            for link in page.locator('a.support-link').all():
                assert link.get_attribute('href') == 'https://ko-fi.com/sunheat'
                assert link.get_attribute('target') == '_blank'
                assert 'noopener' in link.get_attribute('rel')
            assert page.locator('.app-footer .support-link').evaluate("e => parseFloat(getComputedStyle(e).fontSize) === 13")
            page.screenshot(path=str(ROOT / 'build/location-success-dark.png'))
            result.wait_for(state='hidden', timeout=7500)
            page.locator('#set-location').click()
            result.wait_for(state='visible')
            for selector in ['#locationResultSupport', '#locationResultOK']:
                page.locator(selector).hover()
                page.wait_for_function("locationResultAnimation.playState === 'paused'")
                before = page.evaluate('locationResultAnimation.currentTime')
                page.wait_for_timeout(400)
                assert abs(page.evaluate('locationResultAnimation.currentTime') - before) < 1, 'Hover must preserve remaining time'
                page.locator('#locationResultHeading').hover()
                page.wait_for_function("locationResultAnimation.playState === 'running'")
                page.wait_for_timeout(150)
                assert page.evaluate('locationResultAnimation.currentTime') > before, 'Leaving must resume the same countdown'
            page.locator('#locationResultOK').click()
            assert not result.is_visible()
            page.locator('#stop-location').click()
            result.wait_for(state='visible')
            assert page.locator('#locationResultHeading').inner_text() == 'Location restored'
            assert not page.locator('#locationResultSupport').is_visible()
            assert page.evaluate('locationResultAnimation.effect.getTiming().duration') == 3000
            result.wait_for(state='hidden', timeout=4500)

            def fail_location(route):
                route.fulfill(status=503, content_type='application/json', body=json.dumps({'error': '<img src=x onerror="window.errorHTMLExecuted=true"> Device disconnected'}))

            page.route(url + '/set_location', fail_location)
            page.locator('#set-location').click()
            result.wait_for(state='visible')
            assert 'could not confirm' in page.locator('#locationResultMessage').inner_text()
            assert not page.locator('#locationResultSupport').is_visible()
            assert not page.locator('#locationResultDetails').evaluate('e => e.open')
            page.locator('#locationResultDetails summary').click()
            assert '<img' in page.locator('#locationResultTechnical').inner_text()
            assert result.locator('img').count() == 0
            assert not page.evaluate('window.errorHTMLExecuted || false')
            assert not page.locator('#locationResultCountdown').is_visible()
            page.screenshot(path=str(ROOT / 'build/location-error-dark.png'))
            page.keyboard.press('Escape')
            assert not result.is_visible()
            page.unroute(url + '/set_location', fail_location)
            page.locator('#disconnect').click()
            notification = page.locator('#workspaceNotification')
            notification.wait_for(state='visible')
            assert notification.inner_text() == 'Device disconnected'
            assert not result.is_visible()
            box = notification.bounding_box()
            canvas = page.locator('.map-canvas').bounding_box()
            footer = page.locator('.app-footer .support-link').bounding_box()
            assert box['x'] >= canvas['x'] and box['y'] >= canvas['y']
            assert box['y'] + box['height'] < footer['y'], 'Disconnect feedback must not cover the support link'
            page.screenshot(path=str(ROOT / 'build/disconnect-notification-dark.png'))
            notification.wait_for(state='hidden', timeout=5500)
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
            page.evaluate('showLocationResult(false)')
            page.screenshot(path=str(ROOT / 'build/location-success-light.png'))
            page.locator('#locationResultOK').click()
            page.wait_for_timeout(250)
            page.screenshot(path=str(ROOT / 'build/desktop-light.png'))
            page.wait_for_function("document.getElementById('fuelStatus').textContent === ''")
            page.reload(wait_until='networkidle')
            page.wait_for_function("document.getElementById('fuelText').value.includes('Melbourne')")
            assert not page.locator('#darkModeSwitch').is_checked()
            assert page.locator('#fuelRegion').input_value() == 'VIC'
            assert page.locator('#fuelType').input_value() == 'U95'
            page.get_by_role('button', name='Saved places', exact=True).click()
            page.locator('#savePlace').click()
            page.locator('#placeName').fill('<Home & office>')
            page.locator('#placeName').press('ArrowLeft')
            assert page.locator('#coordinates').input_value() == '-37.81, 144.96', 'Editing moved the map pin'
            page.locator('#savePlaceName').click()
            page.wait_for_function("document.querySelectorAll('#savedPlacesList li').length === 1")
            assert page.locator('.place-preview').inner_text() == '<Home & office>'
            page.get_by_role('button', name='Close saved places').click()
            page.reload(wait_until='networkidle')
            page.get_by_role('button', name='Saved places', exact=True).click()
            assert page.locator('.place-preview').inner_text() == '<Home & office>'
            page.get_by_role('button', name='Name <Home & office>', exact=True).click()
            page.locator('#placeName').fill('Home')
            page.locator('#savePlaceName').click()
            page.wait_for_function("document.querySelector('.place-preview').textContent === 'Home'")
            page.locator('.place-preview').click()
            assert not page.locator('#savedPlacesDialog').is_visible()
            assert page.locator('#coordinates').input_value() == '-37.81, 144.96'
            page.get_by_role('button', name='Saved places', exact=True).click()
            page.once('dialog', lambda dialog: dialog.accept())
            page.get_by_role('button', name='Delete Home', exact=True).click()
            page.wait_for_function("document.querySelectorAll('#savedPlacesList li').length === 0")
            page.get_by_role('button', name='Close saved places').click()
            for offset in range(30):
                assert page.request.post(url + '/api/locations', data={'lat': offset, 'lng': 10, 'name': f'Place {offset}'}).status == 200
            page.get_by_role('button', name='Saved places', exact=True).click()
            page.wait_for_function("document.querySelectorAll('#savedPlacesList li').length === 30")
            page.locator('#savePlace').click()
            page.locator('#placeName').fill('One too many')
            page.locator('#savePlaceName').click()
            page.wait_for_function("document.getElementById('placeNameError').textContent.includes('full (30 locations)')")
            assert page.locator('#placeNameError').is_visible(), 'Capacity errors must be visible inside the active dialog'
            assert page.locator('#locationNameDialog').is_visible()
            page.get_by_role('button', name='Cancel', exact=True).click()
            page.get_by_role('button', name='Close saved places').click()
            for place in page.request.get(url + '/api/user_state').json()['locations']:
                assert page.request.delete(url + f"/api/locations/{place['id']}").status == 200
            page.locator('#enableFuelPrices').uncheck()
            page.reload(wait_until='networkidle')
            assert not page.locator('#enableFuelPrices').is_checked()
            assert not page.locator('#fuelType').is_visible()
            page.locator('#enableFuelPrices').check()
            page.wait_for_function("document.getElementById('fuelText').value.includes('Melbourne')")
            print('PASS: preferences survive reload; saved places safely name, preview and delete; editing does not move the pin')
            page.evaluate("""async () => {
                const originalFetch = window.fetch;
                let release;
                window.fetch = (url, options) => url === '/api/fuel_types?region=NSW'
                    ? new Promise(resolve => { release = () => resolve(new Response('["U91"]')); })
                    : originalFetch(url, options);
                try {
                    document.getElementById('fuelRegion').value = 'NSW';
                    const pending = handleFuelTypeChange();
                    document.getElementById('fuelRegion').value = 'VIC';
                    await handleFuelTypeChange();
                    release();
                    await pending;
                } finally { window.fetch = originalFetch; }
            }""")
            page.wait_for_function("document.getElementById('fuelText').value.includes('Melbourne')")
            assert page.locator('#fuelType').input_value() == 'U95', 'A stale region request overwrote the latest selection'
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
        state_directory.cleanup()


if __name__ == "__main__":
    main()
