const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const template = name => fs.readFileSync(path.join(__dirname, '../src/templates', name), 'utf8');
const html = template('map.html');
const start = html.indexOf('    function setLocation() {');
const end = html.indexOf('// Function to enable or disable the Set Location button', start);

async function main() {
    const elements = Object.fromEntries([
        'locationResultDialog', 'locationResultHeading', 'locationResultMessage',
        'locationResultSupport', 'locationResultDetails', 'locationResultTechnical',
        'locationResultCountdown', 'locationResultOK', 'set-location', 'stop-location', 'disconnect',
    ].map(id => [id, {textContent: '', hidden: false, open: false, disabled: false,
        showModal() { this.open = true; },
        close() { this.open = false; this.onclose?.(); }, focus() {},
    }]));
    const toasts = [];
    let response = {ok: false, status: 503, text: async () => '{"error":"<img src=x onerror=alert(1)>"}'};
    let tick;
    let now = 0;
    const context = vm.createContext({
        document: {getElementById: id => elements[id]},
        fetch: async () => response,
        displayToast: message => toasts.push(message), console,
        updateSetLocationButtonStatus() {}, updateStopLocationButtonStatus() {},
        setInterval(callback) { tick = callback; return 1; },
        clearInterval() { tick = null; },
        Date: {now: () => now},
    });
    vm.runInContext(template('workspace.js'), context);
    vm.runInContext(html.slice(start, end), context);
    await context.setLocation();
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(toasts.length, 0, 'HTTP errors must not enter the HTML toast renderer');
    assert.equal(elements.locationResultDialog.open, true);
    assert.equal(elements.locationResultSupport.hidden, true);
    assert.equal(elements.locationResultDetails.open, false);
    assert.match(elements.locationResultTechnical.textContent, /<img/);
    assert.equal(tick, null, 'Errors must wait for acknowledgement');

    response = {ok: true, status: 200, text: async () => 'Location set successfully'};
    await context.setLocation();
    assert.equal(elements.locationResultSupport.hidden, false);
    assert.match(elements.locationResultCountdown.textContent, /6 seconds/);
    now = 5999; tick();
    assert.equal(elements.locationResultDialog.open, true);
    now = 6000; tick();
    assert.equal(elements.locationResultDialog.open, false);
    assert.equal(tick, null);

    response = {ok: true, status: 200, text: async () => 'Location cleared successfully'};
    await context.stopLocation();
    assert.equal(elements.locationResultSupport.hidden, true);
    assert.match(elements.locationResultCountdown.textContent, /3 seconds/);
    elements.locationResultDialog.close();
    assert.equal(tick, null, 'Manual dismissal must cancel the old timer');

    response = {ok: true, status: 200, text: async () => '{"error":"Device unavailable"}'};
    await context.stopLocation();
    assert.equal(elements.locationResultCountdown.hidden, true, 'Unexpected 200 responses must not show success');
    assert.equal(elements.locationResultSupport.hidden, true);
    context.fetch = async () => { throw new Error('Network unavailable'); };
    await context.stopLocation();
    assert.match(elements.locationResultMessage.textContent, /could not confirm/i);
    assert.match(elements.locationResultTechnical.textContent, /Network unavailable/);

    let release;
    let calls = 0;
    context.fetch = () => { calls++; return new Promise(resolve => { release = resolve; }); };
    const pending = context.setLocation();
    assert.equal(elements['set-location'].disabled, true);
    assert.equal(elements['stop-location'].disabled, true);
    assert.equal(elements.disconnect.disabled, true);
    await context.stopLocation();
    assert.equal(calls, 1, 'Pending operations must not overlap');
    release({ok: true, status: 200, text: async () => 'Location set successfully'});
    await pending;
    assert.equal(elements.locationResultDetails.hidden, true);
    assert.equal(elements.locationResultTechnical.textContent, '');
    console.log('PASS: location errors stay literal; confirmed success uses cancellable 6s/3s dialogs');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
