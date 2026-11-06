import St from 'gi://St';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import {parseEvents, dayGroups} from './events.js';

export default class AgendaDesktop extends Extension {
    enable() {
        this._active = true;
        this._process = null;
        this._deadline = 0;
        this._read = null;
        this._events = [];
        this._widget = new St.BoxLayout({vertical: true, width: 340, style_class: 'agenda-widget'});
        this._widget.add_child(new St.Label({text: '📅 Minha Agenda', style_class: 'agenda-title'}));
        this._status = new St.Label({text: 'Carregando agenda…', style_class: 'agenda-status'});
        this._widget.add_child(this._status);
        this._list = new St.BoxLayout({vertical: true, style_class: 'agenda-lista'});
        const scroll = new St.ScrollView({style: 'max-height: 460px;'});
        scroll.set_child(this._list);
        this._widget.add_child(scroll);
        const refresh = new St.Button({label: 'Atualizar eventos', style_class: 'agenda-refresh', can_focus: true});
        refresh.connect('clicked', () => this._update());
        this._widget.add_child(refresh);
        // Public layout API; no _backgroundGroup or other private Shell fields.
        Main.layoutManager.addChrome(this._widget, {affectsStruts: false, trackFullscreen: true});
        this._monitorSignal = Main.layoutManager.connect('monitors-changed', () => this._position());
        this._position();
        this._load();
        this._update();
        this._timer = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 300, () => {
            this._render();
            this._update();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _position() {
        const monitor = Main.layoutManager.primaryMonitor;
        if (monitor)
            this._widget.set_position(monitor.x + Math.max(0, monitor.width - 380), monitor.y + 90);
    }

    _update() {
        if (!this._active || this._process)
            return;
        this._status.set_text('Atualizando…');
        try {
            const process = Gio.Subprocess.new(
                ['/usr/bin/python3', '-B', GLib.build_filenamev([this.path, 'update_events.py'])],
                Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE);
            this._process = process;
            this._deadline = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 60, () => {
                this._deadline = 0;
                if (this._process === process)
                    process.force_exit();
                return GLib.SOURCE_REMOVE;
            });
            process.wait_async(null, (object, result) => {
                let success = false;
                try {
                    object.wait_finish(result);
                    success = object.get_successful();
                } catch (_error) {
                    // Generic status below; never log provider diagnostics.
                }
                if (!this._active || this._process !== process)
                    return;
                this._process = null;
                if (this._deadline)
                    GLib.Source.remove(this._deadline);
                this._deadline = 0;
                if (success)
                    this._load();
                else
                    this._status.set_text('Falha na atualização · dados anteriores');
            });
        } catch (_error) {
            this._status.set_text('Não foi possível iniciar o Core');
        }
    }

    _load() {
        this._read?.cancel();
        const cancellable = new Gio.Cancellable();
        this._read = cancellable;
        const configuredCache = GLib.getenv('XDG_CACHE_HOME');
        const cacheHome = configuredCache && GLib.path_is_absolute(configuredCache)
            ? configuredCache : GLib.build_filenamev([GLib.get_home_dir(), '.cache']);
        const file = Gio.File.new_for_path(GLib.build_filenamev([
            cacheHome, 'agenda-desktop-linux-gnome', 'eventos.json',
        ]));
        file.load_contents_async(cancellable, (object, result) => {
            try {
                const [, bytes] = object.load_contents_finish(result);
                if (!this._active || this._read !== cancellable)
                    return;
                this._events = parseEvents(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
                this._render();
                this._status.set_text('HOJE E AMANHÃ · cache local');
            } catch (_error) {
                if (this._active && this._read === cancellable)
                    this._status.set_text('Cache indisponível ou inválido');
            } finally {
                if (this._read === cancellable)
                    this._read = null;
            }
        });
    }

    _render() {
        this._list.destroy_all_children();
        let count = 0;
        for (const group of dayGroups(this._events)) {
            if (!group.events.length)
                continue;
            this._list.add_child(new St.Label({text: group.title, style_class: 'agenda-dia'}));
            for (const event of group.events.slice(0, 100)) {
                const row = new St.BoxLayout({style_class: 'agenda-evento', x_expand: true});
                const time = event.allDay ? 'Dia todo' : event.start.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
                row.add_child(new St.Label({text: time, style_class: 'agenda-horario', width: 65}));
                const label = new St.Label({text: event.title || 'Sem título', style_class: 'agenda-nome', x_expand: true});
                label.clutter_text.set_line_wrap(true);
                row.add_child(label);
                this._list.add_child(row);
                count++;
            }
            if (group.events.length > 100)
                this._list.add_child(new St.Label({text: 'Exibição limitada a 100 eventos por dia'}));
        }
        if (!count)
            this._list.add_child(new St.Label({text: 'Nenhum compromisso próximo ✨', style_class: 'agenda-vazio'}));
    }

    disable() {
        this._active = false;
        if (this._timer)
            GLib.Source.remove(this._timer);
        if (this._deadline)
            GLib.Source.remove(this._deadline);
        this._timer = this._deadline = 0;
        this._read?.cancel();
        this._read = null;
        this._process?.force_exit();
        this._process = null;
        if (this._monitorSignal)
            Main.layoutManager.disconnect(this._monitorSignal);
        this._monitorSignal = 0;
        Main.layoutManager.removeChrome(this._widget);
        this._widget.destroy();
        this._widget = this._status = this._list = null;
        this._events = [];
    }
}
