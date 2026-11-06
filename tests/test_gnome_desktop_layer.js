import Gio from 'gi://Gio';
import {DesktopLayer, desktopRect, makePassive} from '../desktop/gnome/prototype-desktop/desktopLayer.js';
import {parseEvents, dayGroups} from '../desktop/gnome/events.js';
function assert(value, message) { if (!value) throw new Error(message); }
class Actor {
    constructor(props = {}) {
        this.children = []; this.signals = new Map(); this.next = 1;
        this.parent = null; this.reactive = true; this.can_focus = true; this.track_hover = true;
        Object.assign(this, props);
    }
    connect(name, callback) { const id = this.next++; this.signals.set(id, {name, callback}); return id; }
    disconnect(id) { assert(this.signals.delete(id), 'valid signal disconnected once'); }
    emit(name, ...args) { for (const signal of [...this.signals.values()]) if (signal.name === name) signal.callback(this, ...args); }
    get_parent() { return this.parent; }
    get_children() { return [...this.children]; }
    add_child(child) { child.parent = this; this.children.push(child); this.emit('child-added', child); }
    set_child_above_sibling(child, sibling) {
        assert(sibling === null && child.parent === this, 'raise only own child, within background');
        this.children = this.children.filter(value => value !== child); this.children.push(child);
    }
    set_size(width, height) { this.size = [width, height]; }
    set_position(x, y) { this.position = [x, y]; }
    set_clip(x, y, width, height) { this.clip = [x, y, width, height]; }
    destroy_all_children() { for (const child of [...this.children]) child.destroy(); }
    destroy() {
        if (this.destroyed) throw new Error('double destroy');
        this.emit('destroy'); this.destroy_all_children(); this.signals.clear();
        if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this);
        this.parent = null; this.destroyed = true;
    }
    get clutter_text() { return {set_line_wrap() {}}; }
}
function hierarchy() {
    const windows = new Actor(); const background = new Actor(); const normal = new Actor();
    windows.add_child(background); windows.add_child(normal);
    return {windows, background, normal};
}
const {windows, background, normal} = hierarchy();
const root = new Actor(); root.add_child(new Actor());
const layer = new DesktopLayer(background, windows, root);
assert(windows.children[0] === background && windows.children[1] === normal, 'normal windows stay above background');
assert(!root.reactive && !root.can_focus && !root.children[0].reactive, 'entire subtree is passive');
const wallpaper = new Actor(); background.add_child(wallpaper);
assert(background.children.at(-1) === root, 'wallpaper replacement stays below prototype');
assert(windows.children[1] === normal, 'no manipulation of window order');
layer.setVisible(false); assert(root.visible === false, 'can hide for overview/lock');
layer.setVisible(true); assert(root.visible === true, 'can reveal desktop');
layer.destroy(); layer.destroy();
assert(root.destroyed && background.signals.size === 0 && background.children[0] === wallpaper, 'idempotent cleanup owns no wallpaper');
let failed = false;
try { new DesktopLayer(new Actor(), windows, new Actor()); } catch (_error) { failed = true; }
assert(failed, 'missing hierarchy fails without chrome fallback');
const second = hierarchy(); const removedRoot = new Actor();
const removedLayer = new DesktopLayer(second.background, second.windows, removedRoot);
second.background.destroy();
assert(!removedLayer.attached, 'background destruction detaches layer');
removedLayer.destroy();
for (const area of [{x: -1920, y: -400, width: 1920, height: 1080}, {x: 0, y: 0, width: 180, height: 160}]) {
    const rect = desktopRect(area);
    assert(rect.x >= area.x && rect.y >= area.y && rect.x + rect.width <= area.x + area.width && rect.y + rect.height <= area.y + area.height, 'clamp to work area including negative origins');
}
// Run prototype lifecycle with mocked Shell only. No extension is loaded into Shell.
const h = hierarchy(); const layout = new Actor(); layout._backgroundGroup = h.background;
layout.monitors = [{}, {}];
const overview = new Actor(); overview.visible = false;
const session = new Actor(); session.currentMode = 'user';
const display = new Actor(); const workspaces = new Actor();
workspaces.get_active_workspace = () => ({get_work_area_for_monitor(index) { return {x: index * 1920, y: 28, width: 1920, height: 1052}; }});
const globals = {window_group: h.windows, display, workspace_manager: workspaces, stage: {width: 3840, height: 1080}};
const timers = new Map(); let timerId = 1;
const GLib = {PRIORITY_DEFAULT: 0, SOURCE_CONTINUE: true,
    timeout_add_seconds(_priority, seconds, callback) { const id = timerId++; timers.set(id, {seconds, callback}); return id; },
    Source: {remove(id) { assert(timers.delete(id), 'timer removed once'); }}};
const Main = {layoutManager: layout, overview, sessionMode: session};
const St = {Widget: Actor, BoxLayout: Actor, Label: Actor};
const Config = {PACKAGE_VERSION: '46.0'};
const [, bytes] = Gio.File.new_for_path('desktop/gnome/prototype-desktop/extension.js').load_contents(null);
const source = new TextDecoder().decode(bytes).replace(/^import .*;\n/gm, '').replace('export default class', 'class');
const Prototype = new Function('St', 'GLib', 'Main', 'Config', 'Extension', 'global', 'DesktopLayer', 'desktopRect', 'makePassive', 'parseEvents', 'dayGroups',
    `${source}\nreturn DesktopPrototype;`)(St, GLib, Main, Config, class {}, globals, DesktopLayer, desktopRect, makePassive, parseEvents, dayGroups);
const prototype = new Prototype(); prototype.enable();
assert(prototype._root.children.length === 2 && timers.size === 1, 'one card per monitor and one timer');
const firstRoot = prototype._root;
overview.visible = true; overview.emit('showing'); assert(!firstRoot.visible, 'hide in overview');
overview.visible = false; overview.emit('hidden'); assert(firstRoot.visible, 'restore after overview');
session.currentMode = 'unlock-dialog'; session.emit('updated'); assert(!firstRoot.visible, 'hide when locked');
session.currentMode = 'user'; session.emit('updated'); assert(firstRoot.visible, 'restore on user session');
layout.monitors = [{}]; layout.emit('monitors-changed'); assert(firstRoot.children.length === 1, 'hot unplug rebuilds cards');
workspaces.emit('active-workspace-changed'); assert(firstRoot.children.length === 1, 'same agenda on new workspace');
prototype.disable(); prototype.disable();
assert(timers.size === 0 && firstRoot.destroyed && layout.signals.size === 0 && overview.signals.size === 0 && workspaces.signals.size === 0 && display.signals.size === 0, 'complete idempotent cleanup');
prototype.enable();
h.background.destroy();
for (const timer of timers.values()) timer.callback();
prototype.disable();
assert(timers.size === 0, 'background destruction safely stops rendering until disable');
Config.PACKAGE_VERSION = '47.0';
failed = false; try { prototype.enable(); } catch (_error) { failed = true; }
assert(failed && timers.size === 0, 'unsupported Shell fails closed with cleanup');
print('Desktop layer and prototype lifecycle mock tests passed; real stacking/input remain visual tests');
