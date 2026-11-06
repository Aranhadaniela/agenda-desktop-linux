import St from 'gi://St';
import GLib from 'gi://GLib';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as Config from 'resource:///org/gnome/shell/misc/config.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import {DesktopLayer, desktopRect, makePassive} from './desktopLayer.js';
import {parseEvents, dayGroups} from './events.js';

// Layer-only investigation: synthetic data, no cache, Python, EDS or network.
export default class DesktopPrototype extends Extension {
    enable() {
        this._signals = [];
        this._timer = 0;
        this._root = null;
        this._layer = null;
        try {
            if (Config.PACKAGE_VERSION.split('.')[0] !== '46')
                throw new Error('Desktop prototype requires GNOME Shell 46');
            const background = Main.layoutManager._backgroundGroup;
            if (!background || background.get_parent() !== global.window_group)
                throw new Error('GNOME 46 desktop layer unavailable');
            this._root = new St.Widget({reactive: false, can_focus: false, visible: false});
            this._layer = new DesktopLayer(background, global.window_group, this._root);
            this._connect(Main.layoutManager, 'monitors-changed', () => this._render());
            this._connect(global.display, 'workareas-changed', () => this._render());
            this._connect(global.workspace_manager, 'active-workspace-changed', () => this._render());
            this._connect(Main.overview, 'showing', () => this._syncVisibility());
            this._connect(Main.overview, 'hidden', () => this._syncVisibility());
            this._connect(Main.sessionMode, 'updated', () => this._syncVisibility());
            this._render();
            this._timer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 60, () => {
                this._render();
                return GLib.SOURCE_CONTINUE;
            });
        } catch (error) {
            this.disable();
            throw error;
        }
    }

    _connect(object, signal, callback) {
        this._signals.push([object, object.connect(signal, callback)]);
    }

    _syncVisibility() {
        this._layer?.setVisible(Main.sessionMode.currentMode === 'user' && !Main.overview.visible);
    }

    _syntheticEvents() {
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const date = value => `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
        return parseEvents(JSON.stringify({eventos: [
            {titulo: 'Exemplo: agenda na área de trabalho', inicio: date(today), fim: null, dia_inteiro: true},
            {titulo: 'Exemplo: amanhã · texto literal <b>roxo</b>', inicio: date(tomorrow), fim: null, dia_inteiro: true},
        ]}));
    }

    _render() {
        if (!this._root || !this._layer?.attached)
            return;
        this._root.set_size(global.stage.width, global.stage.height);
        this._root.destroy_all_children();
        const workspace = global.workspace_manager.get_active_workspace();
        const groups = dayGroups(this._syntheticEvents());
        // One card per logical monitor, same data on all workspaces. No window movement.
        for (let index = 0; index < Main.layoutManager.monitors.length; index++) {
            const rect = desktopRect(workspace.get_work_area_for_monitor(index));
            const card = new St.BoxLayout({vertical: true, style_class: 'agenda-widget', reactive: false, can_focus: false});
            card.set_position(rect.x, rect.y);
            card.set_size(rect.width, rect.height);
            card.set_clip(0, 0, rect.width, rect.height);
            card.add_child(new St.Label({text: 'Minha Agenda', style_class: 'agenda-title'}));
            card.add_child(new St.Label({text: 'PROTÓTIPO · DADOS SINTÉTICOS', style_class: 'agenda-status'}));
            for (const group of groups) {
                card.add_child(new St.Label({text: group.title, style_class: 'agenda-dia'}));
                for (const event of group.events) {
                    const label = new St.Label({text: `Dia todo · ${event.title}`, style_class: 'agenda-nome'});
                    label.clutter_text.set_line_wrap(true);
                    card.add_child(label);
                }
            }
            this._root.add_child(card);
        }
        makePassive(this._root);
        this._layer.raiseWithinBackground();
        this._syncVisibility();
    }

    disable() {
        if (this._timer)
            GLib.Source.remove(this._timer);
        this._timer = 0;
        for (const [object, id] of this._signals ?? [])
            object.disconnect(id);
        this._signals = [];
        if (this._layer)
            this._layer.destroy();
        else
            this._root?.destroy();
        this._layer = this._root = null;
    }
}
