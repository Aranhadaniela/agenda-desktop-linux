// Headless contract tests: trusted local source, fake Shell/Gio objects, no activation.
import RealGio from 'gi://Gio';
import {parseEvents, dayGroups} from '../desktop/gnome/events.js';
function assert(value, message) {
    if (!value)
        throw new Error(message);
}
let nextId = 1;
const timers = new Map();
const signals = new Map();
const chrome = new Set();
const processes = [];
const reads = [];
let spawnFails = false;
class Actor {
    constructor(props = {}) { Object.assign(this, props); this.children = []; }
    add_child(child) { this.children.push(child); }
    set_child(child) { this.children = [child]; }
    connect() { return 1; }
    set_position() {}
    set_text(text) { this.text = text; }
    destroy_all_children() { this.children = []; }
    destroy() { this.destroyed = true; }
    get clutter_text() { return {set_line_wrap() {}}; }
}
const St = {BoxLayout: Actor, Label: Actor, ScrollView: Actor, Button: Actor};
const GLib = {
    PRIORITY_DEFAULT: 0, SOURCE_CONTINUE: true, SOURCE_REMOVE: false,
    timeout_add_seconds(_priority, seconds, callback) {
        const id = nextId++;
        timers.set(id, {seconds, callback});
        return id;
    },
    Source: {remove(id) { assert(timers.delete(id), 'source removed once'); }},
    build_filenamev(parts) { return parts.join('/'); },
    getenv() { return null; },
    get_home_dir() { return '/synthetic-home'; },
    path_is_absolute(path) { return path.startsWith('/'); },
};
const Main = {layoutManager: {
    primaryMonitor: {x: 0, y: 0, width: 1920},
    addChrome(actor) { chrome.add(actor); },
    removeChrome(actor) { assert(chrome.delete(actor), 'remove owned chrome'); },
    connect(_name, callback) { const id = nextId++; signals.set(id, callback); return id; },
    disconnect(id) { assert(signals.delete(id), 'disconnect owned signal'); },
}};
class Cancellable {
    cancel() { this.cancelled = true; }
}
const Gio = {
    Cancellable,
    SubprocessFlags: {STDOUT_SILENCE: 1, STDERR_SILENCE: 2},
    Subprocess: {new(argv) {
        if (spawnFails)
            throw new Error('synthetic spawn failure');
        const process = {
            argv, killed: false, success: false,
            wait_async(_cancel, callback) { this.callback = callback; },
            wait_finish() {}, get_successful() { return this.success; },
            force_exit() { this.killed = true; },
            finish(success) { this.success = success; this.callback(this, {}); },
        };
        processes.push(process);
        return process;
    }},
    File: {new_for_path() { return {
        load_contents_async(cancellable, callback) {
            const read = {cancellable, callback, object: this};
            reads.push(read);
        },
        load_contents_finish(result) {
            if (result.error)
                throw new Error('synthetic invalid cache');
            return [true, new TextEncoder().encode(result.text ?? '{"eventos":[]}')];
        },
    }; }},
};
class Extension { constructor() { this.path = '/synthetic-package'; } }
const [, bytes] = RealGio.File.new_for_path('desktop/gnome/extension.js').load_contents(null);
const source = new TextDecoder().decode(bytes).replace(/^import .*;\n/gm, '').replace('export default class', 'class');
// Does not evaluate GI/Shell imports: dependencies above are injected mocks.
const Agenda = new Function('St', 'Gio', 'GLib', 'Main', 'Extension', 'parseEvents', 'dayGroups',
    `${source}\nreturn AgendaDesktop;`)(St, Gio, GLib, Main, Extension, parseEvents, dayGroups);
function finishRead(read, result = {}) { read.callback(read.object, result); }
const agenda = new Agenda();
agenda.enable();
assert(processes.length === 1 && timers.size === 2 && chrome.size === 1, 'enable creates one update/timer/widget');
agenda._update(); agenda._update();
assert(processes.length === 1, 'rapid clicks never spawn duplicate');
assert(processes[0].argv[0] === '/usr/bin/python3' && processes[0].argv.at(-1).endsWith('/update_events.py'), 'fixed argv');
finishRead(reads[0], {error: true});
assert(agenda._status.text.includes('indisponível'), 'missing cache is handled');
processes[0].finish(true);
finishRead(reads.at(-1));
assert(agenda._status.text.includes('cache local') && timers.size === 1, 'successful update reads cache and removes timeout');
agenda._update();
const timeout = agenda._deadline;
const sourceTimeout = timers.get(timeout);
timers.delete(timeout); // GLib removes source when callback returns SOURCE_REMOVE.
assert(sourceTimeout.callback() === false && processes[1].killed, 'timeout stops client');
processes[1].finish(false);
assert(agenda._status.text.includes('Falha') && timers.size === 1, 'failed update keeps retry timer');
agenda._load();
const oldRead = reads.at(-1);
agenda._update();
const oldProcess = processes.at(-1);
agenda.disable();
assert(oldRead.cancellable.cancelled && oldProcess.killed, 'disable cancels IO and process');
assert(timers.size === 0 && signals.size === 0 && chrome.size === 0, 'disable clears all registered resources');
agenda.enable();
const activeProcess = agenda._process;
const activeStatus = agenda._status.text;
finishRead(oldRead, {error: true});
oldProcess.finish(false);
assert(agenda._process === activeProcess && agenda._status.text === activeStatus, 'old callbacks cannot mutate new session');
agenda.disable();
spawnFails = true;
agenda.enable();
assert(agenda._status.text.includes('iniciar') && agenda._process === null, 'spawn error handled');
agenda.disable();
assert(timers.size === 0 && signals.size === 0 && chrome.size === 0, 'cleanup after spawn failure');
print('GNOME lifecycle mock tests passed (not a visual Shell test)');
