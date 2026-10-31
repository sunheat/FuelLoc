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
        'locationResultCountdown', 'locationResultRing', 'locationResultOK', 'workspaceNotification',
        'set-location', 'stop-location', 'disconnect',
    ].map(id => [id, {textContent: '', hidden: false, open: false, disabled: false,
        showModal() { this.open = true; },
        close() { this.open = false; this.onclose?.(); }, focus() {},
        matches() { return this.hovered || false; },
        toggleAttribute(name, value) { this[name] = value; },
    }]));
    const toasts = [];
    let response = {ok: false, status: 503, text: async () => '{"error":"<img src=x onerror=alert(1)>"}'};
    let animation;
    let notificationTimeout;
    elements.locationResultRing.animate = (frames, options) => {
        animation = {frames, options, playState: 'running',
            pause() { this.playState = 'paused'; },
            play() { this.playState = 'running'; },
            cancel() { this.playState = 'idle'; },
        };
        return animation;
    };
    const context = vm.createContext({
        document: {getElementById: id => elements[id]},
        fetch: async () => response,
        displayToast: message => toasts.push(message), console,
        updateSetLocationButtonStatus() {}, updateStopLocationButtonStatus() {},
        setTimeout(callback, duration) { notificationTimeout = {callback, duration}; return 1; }, clearTimeout() {},
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
    assert.equal(animation, undefined, 'Errors must wait for acknowledgement');

    response = {ok: true, status: 200, text: async () => 'Location set successfully'};
    await context.setLocation();
    assert.equal(elements.locationResultSupport.hidden, false);
    assert.equal(elements.locationResultMessage.hidden, false);
    assert.equal(elements.locationResultMessage.textContent, 'Enjoy! Use Stop Location to restore your real location.');
    assert.equal(animation.options.duration, 6000);
    assert.equal(animation.frames[1].strokeDashoffset, -100, 'The ring must recede clockwise');
    for (const id of ['locationResultSupport', 'locationResultOK']) {
        elements[id].hovered = true;
        context.updateLocationCountdownPause();
        assert.equal(animation.playState, 'paused');
        elements[id].hovered = false;
        context.updateLocationCountdownPause();
        assert.equal(animation.playState, 'running');
    }
    animation.onfinish();
    assert.equal(elements.locationResultDialog.open, false);
    assert.equal(animation.playState, 'idle');

    response = {ok: true, status: 200, text: async () => 'Location cleared successfully'};
    await context.stopLocation();
    assert.equal(elements.locationResultSupport.hidden, true);
    assert.equal(animation.options.duration, 3000);
    assert.equal(elements.locationResultMessage.hidden, true, 'Restoration keeps its concise presentation');
    elements.locationResultDialog.close();
    assert.equal(animation.playState, 'idle', 'Manual dismissal must cancel the old timer');

    await context.stopLocation(true);
    assert.equal(elements.locationResultDialog.open, false, 'Disconnect success must not open the restore modal');
    assert.equal(elements.workspaceNotification.hidden, false);
    assert.equal(elements.workspaceNotification.textContent, 'Device disconnected');
    assert.equal(notificationTimeout.duration, 4000);
    notificationTimeout.callback();
    assert.equal(elements.workspaceNotification.hidden, true);

    response = {ok: true, status: 200, text: async () => '{"error":"Device unavailable"}'};
    await context.stopLocation(true);
    assert.equal(elements.locationResultCountdown.hidden, true, 'Unexpected 200 responses must not show success');
    assert.equal(elements.locationResultDialog.open, true, 'Disconnect failures must still show an error dialog');
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
    console.log('PASS: literal errors, concise success, pausable 6s/3s rings, and nonmodal disconnect feedback');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
