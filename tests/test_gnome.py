import importlib.util
import fcntl
import sys
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.install_gnome import build, UUID, ROOT, CORE_FILES

spec = importlib.util.spec_from_file_location('gnome_update', Path(__file__).resolve().parents[1] / 'desktop/gnome/update_events.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class GnomeAdapterTests(unittest.TestCase):
    def test_build_allowlist_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / UUID
            build(target)
            files = {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
            self.assertEqual(len(files), 14)
            self.assertIn('python/core/calendar_service.py', files)
            for name in CORE_FILES:
                self.assertEqual((target / 'python' / name).read_bytes(), (ROOT / name).read_bytes())
            self.assertEqual([name for name in files if name.endswith('.json')], ['metadata.json'])
            for p in target.rglob('*'):
                if p.is_file():
                    self.assertEqual(p.stat().st_mode & 0o777, 0o644)
            with self.assertRaises(FileExistsError):
                build(target)

    def test_private_cache_and_rejects_public_directory(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'XDG_CACHE_HOME': folder}):
            cache = runner.private_cache()
            self.assertEqual(cache.stat().st_mode & 0o777, 0o700)
            cache.chmod(0o755)
            with self.assertRaises(ValueError):
                runner.private_cache()

    def test_cache_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'XDG_CACHE_HOME': folder}):
            actual = Path(folder) / 'actual'
            actual.mkdir(mode=0o700)
            (Path(folder) / 'agenda-desktop-linux-gnome').symlink_to(actual)
            with self.assertRaises(ValueError):
                runner.private_cache()

    def test_config_private_selection_and_no_interpolation(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'XDG_CONFIG_HOME': folder}):
            path = Path(folder) / 'agenda-desktop-linux/gnome.ini'
            path.parent.mkdir(mode=0o700)
            path.write_text('[calendar]\nuid = synthetic-%-uid\n')
            path.chmod(0o600)
            self.assertEqual(runner.calendar_uid(), 'synthetic-%-uid')
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                runner.calendar_uid()

    def test_relative_xdg_uses_home(self):
        with patch.dict(os.environ, {'XDG_CACHE_HOME': 'relative'}):
            self.assertEqual(runner.xdg_dir('XDG_CACHE_HOME', '.cache'), Path.home() / '.cache')

    def test_existing_lock_prevents_second_update(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'XDG_CACHE_HOME': folder}), patch.object(sys, 'path', list(sys.path)):
            cache = runner.private_cache()
            with (cache / 'update.lock').open('w') as lock:
                (cache / 'update.lock').chmod(0o600)
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.assertEqual(runner.main(), 75)
            self.assertFalse((cache / 'eventos.json').exists())

    def test_default_installer_only_builds_and_preserves_fake_installation(self):
        import shutil
        from scripts import install_gnome
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            checkout = base / 'checkout'
            data = base / 'data'
            current = data / 'gnome-shell/extensions/existing-test-extension'
            current.mkdir(parents=True)
            sentinel = current / 'sentinel'
            sentinel.write_text('preserve')
            sources = ['LICENSE', *CORE_FILES, *['desktop/gnome/' + name for name in install_gnome.EXTENSION_FILES]]
            for name in sources:
                target = checkout / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            with patch.object(install_gnome, 'ROOT', checkout), patch.object(sys, 'argv', ['install_gnome.py']), patch.dict(os.environ, {'XDG_DATA_HOME': str(data)}):
                install_gnome.main()
                self.assertTrue((checkout / 'dist/gnome' / UUID / 'extension.js').exists())
                with self.assertRaises(SystemExit) as error:
                    install_gnome.main()
                self.assertEqual(error.exception.code, 2)
            self.assertEqual(sentinel.read_text(), 'preserve')
            self.assertEqual(list(current.parent.iterdir()), [current])

    def test_synthetic_bundled_runner_never_imports_evolution_or_gi(self):
        import json
        import subprocess
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            package = build(base / 'package')
            config = base / 'config/agenda-desktop-linux/gnome.ini'
            config.parent.mkdir(parents=True)
            config.write_text('[calendar]\nsource = synthetic\n')
            config.chmod(0o600)
            env = {**os.environ, 'XDG_CONFIG_HOME': str(base / 'config'), 'XDG_CACHE_HOME': str(base / 'cache')}
            code = """
import builtins, runpy, sys
original = builtins.__import__
def checked(name, *args, **kwargs):
    if name == 'gi' or name.startswith('gi.') or name == 'providers.evolution':
        raise AssertionError('EDS/GI must not be imported')
    return original(name, *args, **kwargs)
builtins.__import__ = checked
runpy.run_path(sys.argv[1], run_name='__main__')
"""
            result = subprocess.run(['/usr/bin/python3', '-I', '-c', code, str(package / 'update_events.py')], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            output = base / 'cache/agenda-desktop-linux-gnome/eventos.json'
            data = json.loads(output.read_text())
            self.assertEqual(len(data['eventos']), 4)
            self.assertTrue(all(event['titulo'].startswith('Exemplo:') for event in data['eventos']))
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_unknown_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'XDG_CONFIG_HOME': folder}):
            path = Path(folder) / 'agenda-desktop-linux/gnome.ini'
            path.parent.mkdir()
            path.write_text('[calendar]\nsource = typo\n')
            path.chmod(0o600)
            with self.assertRaises(ValueError):
                runner.selection()
