// Parse with the same SpiderMonkey engine as GJS, without importing or enabling Shell UI.
import Gio from 'gi://Gio';
for (const name of ARGV) {
    const [, bytes] = Gio.File.new_for_path(name).load_contents(null);
    Reflect.parse(new TextDecoder().decode(bytes), {target: 'module'});
    print(`Syntax OK: ${name}`);
}
