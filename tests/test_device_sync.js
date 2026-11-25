const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../src/templates/map.html'), 'utf8');
const scan = html.slice(html.indexOf('async function populateDeviceList()'), html.indexOf('// Checkbox visibility toggle'));
const disconnect = html.slice(html.indexOf('    async function disconnectDevice()'), html.indexOf('    let fuelRequestId'));
const elements = Object.fromEntries(['device', 'connect', 'connectText', 'disconnect', 'rsdData',
    'set-location', 'stop-location', 'connectError'].map(id => [id, {
    value: '', disabled: false, style: {}, options: [], textContent: '',
    add(option) { this.options.push(option); if (!this.value) this.value = option.value; },
    set innerHTML(value) { this.options = []; this.value = ''; },
}]));
const phone = {Identifier: 'test-device', ConnectionType: 'USB', DeviceName: 'Phone', ProductVersion: '18.0'};
let snapshot = {devices: {'test-device': {USB: [phone]}}, udid: 'test-device', rsd_data: 'fd00::1:1234'};
let disconnectOK = true;
const requests = [];
const context = vm.createContext({
    document: {getElementById: id => elements[id]}, console,
    Option: function(text, value) { this.text = text; this.value = value; },
    AbortSignal: {timeout() {}},
    fetch: async (url, options) => {
        requests.push([url, options?.method]);
        return {ok: url !== '/stop_tunnel' || disconnectOK, json: async () => snapshot,
            text: async () => 'Restoration failed'};
    },
    updateSetLocationButtonStatus() { elements['set-location'].disabled = !elements.rsdData.value; },
    updateStopLocationButtonStatus() { elements['stop-location'].disabled = !elements.rsdData.value; },
    showWorkspaceNotification() {}, showLocationResult() {}, stopLocation() {},
    deviceActionPending: false, deviceStatusPending: false, deviceStateRevision: 0, locationActionPending: false,
});
vm.runInContext(scan + disconnect, context);

(async () => {
    await context.populateDeviceList();
    assert.equal(elements.rsdData.value, 'fd00::1:1234', 'Status must come from the backend session');
    assert.equal(elements.device.disabled, true);
    snapshot = {devices: {}, udid: null, rsd_data: ''};
    await context.populateDeviceList();
    assert.equal(elements.rsdData.value, '', 'Cable loss must clear the stale connected marker');
    assert.equal(elements['set-location'].disabled, true);
    assert.equal(elements.device.disabled, false);
    snapshot.devices = {'test-device': {USB: [phone]}};
    await context.populateDeviceList();
    assert.equal(elements.device.options.length, 1, 'A replugged phone must return without Refresh');
    assert.equal(elements.rsdData.value, '', 'Discovery alone must not claim a connected session');
    requests.length = 0;
    await context.disconnectDevice();
    assert(requests.some(([url, method]) => url === '/stop_tunnel' && method === 'POST'),
        'Manual disconnect must actually close the tunnel');

    // A poll started before Connect must never overwrite that newer operation.
    let resolveStatus;
    context.fetch = () => new Promise(resolve => { resolveStatus = resolve; });
    const pending = context.populateDeviceList();
    context.deviceStateRevision++;
    elements.rsdData.value = 'new-session';
    resolveStatus({ok: true, json: async () => ({devices: {}, udid: null, rsd_data: ''})});
    await pending;
    assert.equal(elements.rsdData.value, 'new-session');
    console.log('PASS: cable loss, replug discovery, real disconnect and stale poll protection');
})().catch(error => { console.error(error); process.exitCode = 1; });
