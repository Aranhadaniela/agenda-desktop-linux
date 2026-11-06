// GNOME 46 compatibility boundary. No Shell globals or I/O in this module.
export function desktopRect(area, preferredWidth = 340, preferredHeight = 440, margin = 16) {
    if (![area.x, area.y, area.width, area.height].every(Number.isFinite) || area.width <= 0 || area.height <= 0)
        throw new Error('Invalid desktop geometry');
    const inset = Math.min(margin, area.width / 4, area.height / 4);
    const width = Math.min(preferredWidth, area.width - inset * 2);
    const height = Math.min(preferredHeight, area.height - inset * 2);
    return {x: area.x + area.width - inset - width, y: area.y + inset, width, height};
}

export function makePassive(actor) {
    actor.reactive = false;
    if ('can_focus' in actor)
        actor.can_focus = false;
    if ('track_hover' in actor)
        actor.track_hover = false;
    for (const child of actor.get_children())
        makePassive(child);
}

export class DesktopLayer {
    constructor(backgroundGroup, windowGroup, root) {
        if (!backgroundGroup || backgroundGroup.get_parent() !== windowGroup || windowGroup.get_children()[0] !== backgroundGroup || root.get_parent())
            throw new Error('GNOME 46 desktop hierarchy unavailable; no overlay fallback');
        this._windowGroup = windowGroup;
        this._background = backgroundGroup;
        this._root = root;
        this._signals = [];
        makePassive(root);
        try {
            backgroundGroup.add_child(root);
            this._signals.push(backgroundGroup.connect('child-added', () => this.raiseWithinBackground()));
            this._signals.push(backgroundGroup.connect('destroy', () => {
                // Children are destroyed by Clutter with their parent.
                this._background = null;
                this._root = null;
                this._signals = [];
            }));
            this.raiseWithinBackground();
        } catch (error) {
            this.destroy();
            throw error;
        }
    }

    get attached() {
        return Boolean(this._background && this._root &&
            this._background.get_parent() === this._windowGroup &&
            this._windowGroup.get_children()[0] === this._background &&
            this._root.get_parent() === this._background);
    }

    raiseWithinBackground() {
        if (this.attached)
            this._background.set_child_above_sibling(this._root, null);
    }

    setVisible(visible) {
        if (this._root)
            this._root.visible = Boolean(visible && this.attached);
    }

    destroy() {
        if (this._background) {
            for (const id of this._signals)
                this._background.disconnect(id);
        }
        this._signals = [];
        this._root?.destroy();
        this._root = this._background = this._windowGroup = null;
    }
}
