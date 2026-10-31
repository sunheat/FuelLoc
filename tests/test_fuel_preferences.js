const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const readTemplate = name => fs.readFileSync(path.join(__dirname, '../src/templates', name), 'utf8');
const html = readTemplate('map.html');
const desktop = readTemplate('desktop.html');
const workspace = readTemplate('workspace.js');
const start = html.indexOf('let fuelRequestId = 0;');
const end = html.indexOf('async function updateFuelText(', start);
assert(start >= 0 && end > start);

async function checkPreferences() {
    const fuelType = {
        value: '',
        set innerHTML(value) { this.value = ''; },
        add(option) { if (!this.value) this.value = option.value; },
    };
    const elements = {
        fuelType,
        fuelRegion: { value: 'All' },
        fuelText: { value: '' },
        fuelStatus: { textContent: '' },
        fuelDataCollapse: { classList: { remove() {} } },
    };
    const stored = { fuel_type: 'U95', fuel_region: 'All' };
    const previews = [];
    const context = vm.createContext({
        document: { getElementById: id => elements[id], createElement: () => ({}) },
        console,
        displayToast(message) { throw new Error(message); },
        updateFuelText(type, region) { previews.push({ type, region }); },
        async fetch(url, options) {
            if (url === '/api/preferences') {
                Object.assign(stored, JSON.parse(options.body));
                return { ok: true, json: async () => stored };
            }
            const region = new URL(url, 'http://localhost').searchParams.get('region');
            return { ok: true, json: async () => region === 'WA' ? ['U91'] : ['U91', 'U95'] };
        },
    });
    vm.runInContext(workspace.slice(0, workspace.indexOf('async function loadWorkspaceState()')), context);
    vm.runInContext(html.slice(start, end), context);
    async function change(id, value) {
        elements[id].value = value;
        const handler = desktop.match(new RegExp(`id="${id}" onchange="([^"]+)"`));
        assert(handler, `Missing change handler for ${id}`);
        await vm.runInContext(handler[1], context);
        await vm.runInContext('preferenceWrites', context);
    }
    async function reload() {
        fuelType.value = '';
        context.savedPreferences = { ...stored };
        vm.runInContext('workspacePreferences = savedPreferences', context);
        await context.handleFuelTypeChange();
        await vm.runInContext('preferenceWrites', context);
    }

    await reload();
    assert.equal(fuelType.value, 'U95');
    await change('fuelRegion', 'WA');
    assert.equal(fuelType.value, 'U91', 'Unavailable preference should display a fallback');
    assert.equal(stored.fuel_type, 'U95', 'A regional fallback must not replace the saved preference');
    await change('fuelRegion', 'All');
    assert.equal(fuelType.value, 'U95', 'Returning directly from a fallback region must restore U95');
    await change('fuelRegion', 'WA');
    await reload();
    assert.equal(stored.fuel_type, 'U95', 'Reloading a fallback region must preserve the preference');
    await change('fuelRegion', 'All');
    assert.equal(fuelType.value, 'U95', 'Returning to All Australia must restore U95');
    assert.deepEqual(previews.at(-1), { type: 'U95', region: 'All' });
    await change('fuelRegion', 'WA');
    await change('fuelType', 'U91');
    assert.equal(stored.fuel_type, 'U91', 'An explicit fuel selection must update the preference');
    await change('fuelRegion', 'All');
    await reload();
    assert.equal(fuelType.value, 'U91', 'Explicit preference must survive region changes and reloads');
    console.log('Fuel preferences survive regional fallbacks and change only on explicit selection');
}

checkPreferences().catch(error => { console.error(error); process.exitCode = 1; });
