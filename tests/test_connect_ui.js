const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../src/templates/map.html'), 'utf8');
const start = html.indexOf('function connectDevice() {');
const end = html.indexOf('// Function to show the modal for developer mode required', start);
assert(start >= 0 && end > start);
assert(fs.readFileSync(path.join(__dirname, '../src/templates/desktop.html'), 'utf8').includes('id="connectError"'), 'The connection error needs a visible status element');

async function checkFailure(fetch, expectedError) {
    const elements = {
        connect: { disabled: false },
        connectText: { innerText: 'Connect Device', style: {} },
        spinner: { style: { display: 'none' } },
        device: { value: JSON.stringify({ Identifier: 'test-device', ConnectionType: 'USB' }) },
        connectError: { textContent: '' },
    };
    const context = {
        document: { getElementById: id => elements[id] || null },
        fetch,
        AbortSignal: { timeout: () => ({}) },
        console: { log() {}, error() {} },
        displayToast() {},
        showModalTimeout() {},
        showModalDeveloperModeRequired() {},
        showPairRecordModal() {},
    };
    vm.runInNewContext(html.slice(start, end), context);
    context.connectDevice();
    await new Promise(resolve => setTimeout(resolve, 0));
    assert.equal(elements.spinner.style.display, 'none', 'Connection spinner must stop on failure');
    assert.match(elements.connectError.textContent, expectedError);
    assert.equal(elements.connect.disabled, false);
}

(async () => {
    await checkFailure(() => Promise.resolve({ json: async () => ({ error: 'Device is busy' }) }), /Device is busy/);
    await checkFailure(() => Promise.reject(new Error('Network unavailable')), /Network unavailable/);
    console.log('Connection failures show their cause and stop the spinner');
})().catch(error => { console.error(error); process.exitCode = 1; });
