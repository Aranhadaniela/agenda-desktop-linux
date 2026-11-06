import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.build_gnome_desktop_prototype import build, SOURCES, UUID, ROOT


class DesktopPrototypePackageTests(unittest.TestCase):
    def test_closed_synthetic_package(self):
        with tempfile.TemporaryDirectory() as folder:
            target = build(Path(folder) / UUID)
            files = {p.name for p in target.iterdir()}
            self.assertEqual(files, set(SOURCES))
            for name, source in SOURCES.items():
                self.assertEqual((target / name).read_bytes(), (ROOT / source).read_bytes())
                self.assertEqual((target / name).stat().st_mode & 0o777, 0o644)
            meta = json.loads((target / 'metadata.json').read_text())
            self.assertEqual(meta['uuid'], UUID)
            self.assertEqual(meta['shell-version'], ['46'])
            self.assertNotIn('python', files)
            self.assertNotIn('update_events.py', files)
            with self.assertRaises(FileExistsError):
                build(target)

    def test_preparation_cannot_write_to_extension_root(self):
        with tempfile.TemporaryDirectory() as folder, patch('scripts.build_gnome_desktop_prototype.data_home', return_value=Path(folder)):
            target = Path(folder) / 'gnome-shell/extensions' / UUID
            with self.assertRaises(ValueError):
                build(target)
            self.assertFalse(target.exists())

    def test_reproducible_zip_contains_exact_reviewed_files(self):
        from scripts.build_gnome_desktop_prototype import create_archive
        from zipfile import ZipFile
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            package = build(base / UUID)
            first, second = base / 'first.zip', base / 'second.zip'
            self.assertEqual(create_archive(package, first), create_archive(package, second))
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with ZipFile(first) as bundle:
                self.assertEqual(set(bundle.namelist()), set(SOURCES))
                self.assertEqual(len(bundle.namelist()), 6)
                for name, source in SOURCES.items():
                    self.assertEqual(bundle.read(name), (ROOT / source).read_bytes())
                    self.assertEqual((bundle.getinfo(name).external_attr >> 16) & 0o777, 0o644)
            original = first.read_bytes()
            with self.assertRaises(FileExistsError):
                create_archive(package, first)
            self.assertEqual(first.read_bytes(), original)

    def test_archive_rejects_additional_or_modified_files(self):
        from scripts.build_gnome_desktop_prototype import create_archive
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            package = build(base / UUID)
            extra = package / 'unexpected.txt'
            extra.write_text('synthetic')
            with self.assertRaises(ValueError):
                create_archive(package, base / 'extra.zip')
            extra.unlink()
            (package / 'events.js').write_text('modified synthetic file')
            with self.assertRaises(ValueError):
                create_archive(package, base / 'modified.zip')
            self.assertFalse((base / 'extra.zip').exists())
            self.assertFalse((base / 'modified.zip').exists())

    def test_archive_rejects_symlink_and_nested_archive(self):
        from scripts.build_gnome_desktop_prototype import create_archive
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            package = build(base / UUID)
            with self.assertRaises(ValueError):
                create_archive(package, package / 'inside.zip')
            alias = base / 'alias'
            alias.symlink_to(package, target_is_directory=True)
            with self.assertRaises(ValueError):
                create_archive(alias, base / 'alias.zip')
