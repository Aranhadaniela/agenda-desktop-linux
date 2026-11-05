import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from core.calendar_service import CalendarService
from core.json_writer import write_events
from core.models import CalendarEvent


class ServiceTests(unittest.TestCase):
    def test_rejects_nonpositive_days(self):
        provider = Mock()
        for days in (0, -1):
            with self.assertRaises(ValueError):
                CalendarService(provider).get_upcoming_events(days)
        provider.get_events.assert_not_called()

    def test_queries_midnight_window_and_sorts(self):
        early = CalendarEvent('Primeiro', '2026-11-05T08:00:00-03:00', None)
        late = CalendarEvent('Segundo', '2026-11-05T09:00:00-03:00', None)
        provider = Mock()
        provider.get_events.return_value = [late, early]
        self.assertEqual(CalendarService(provider).get_upcoming_events(2), [early, late])
        start, end = provider.get_events.call_args.args
        self.assertEqual(start.hour, 0)
        self.assertIsNotNone(start.tzinfo)
        self.assertEqual((end.date() - start.date()).days, 2)

    def test_provider_error_propagates(self):
        provider = Mock()
        provider.get_events.side_effect = RuntimeError('indisponível')
        with self.assertRaises(RuntimeError):
            CalendarService(provider).get_upcoming_events()


class WriterTests(unittest.TestCase):
    def test_schema_unicode_and_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'sub' / 'events.json'
            event = CalendarEvent('Reunião', '2026-11-05', None, True)
            write_events([event], output)
            self.assertEqual(json.loads(output.read_text()), {'eventos': [
                {'titulo': 'Reunião', 'inicio': '2026-11-05', 'fim': None, 'dia_inteiro': True}]})
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            write_events([], output)
            self.assertEqual(json.loads(output.read_text()), {'eventos': []})

    def test_replace_failure_preserves_original_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'events.json'
            output.write_text('original')
            with patch('core.json_writer.os.replace', side_effect=OSError('falha')):
                with self.assertRaises(OSError):
                    write_events([], output)
            self.assertEqual(output.read_text(), 'original')
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_serialization_failure_preserves_original_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'events.json'
            output.write_text('original')
            with patch('core.json_writer.json.dump', side_effect=TypeError('falha')):
                with self.assertRaises(TypeError):
                    write_events([], output)
            self.assertEqual(output.read_text(), 'original')
            self.assertEqual(list(Path(directory).iterdir()), [output])


class WriterSecurityTests(unittest.TestCase):
    def test_fsync_failure_preserves_original_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'events.json'
            output.write_text('original')
            with patch('core.json_writer.os.fsync', side_effect=OSError('falha')):
                with self.assertRaises(OSError):
                    write_events([], output)
            self.assertEqual(output.read_text(), 'original')
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_replaces_symlink_without_writing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'target'
            target.write_text('original')
            output = Path(directory) / 'events.json'
            output.symlink_to(target)
            write_events([], output)
            self.assertFalse(output.is_symlink())
            self.assertEqual(target.read_text(), 'original')
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_replacing_public_file_restricts_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'events.json'
            output.write_text('original')
            output.chmod(0o644)
            write_events([], output)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)


if __name__ == '__main__':
    unittest.main()
