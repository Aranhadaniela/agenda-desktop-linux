import unittest
from datetime import datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from core.calendar_service import CalendarService
from core.models import CalendarEvent


class DateTests(unittest.TestCase):
    def test_offsets_dates_and_floating_times(self):
        provider = Mock()
        events = [CalendarEvent(str(i), start, None) for i, start in enumerate([
            '2026-11-05T09:00:00+00:00', '2026-11-05T07:00:00-03:00',
            '2026-11-05', '2026-11-05T05:00:00'])]
        provider.get_events.return_value = events
        result = CalendarService(provider, tz=ZoneInfo('America/Fortaleza')).get_upcoming_events()
        self.assertEqual(result, [events[2], events[3], events[0], events[1]])

    def test_window_crosses_dst_in_calendar_days(self):
        for day, hours in [(8, 47), (1, 49)]:
            month = 3 if day == 8 else 11
            tz = ZoneInfo('America/New_York')
            provider = Mock()
            provider.get_events.return_value = []
            service = CalendarService(provider, tz=tz, clock=lambda: datetime(2026, month, day, 12, tzinfo=tz))
            service.get_upcoming_events(2)
            start, end = provider.get_events.call_args.args
            self.assertEqual((end.timestamp() - start.timestamp()) / 3600, hours)


try:
    from providers.evolution import EvolutionProvider
    from gi.repository import ICalGLib
except (ImportError, ValueError):
    EvolutionProvider = None


@unittest.skipIf(EvolutionProvider is None, 'Bindings EDS indisponíveis')
class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.provider = EvolutionProvider(tz=ZoneInfo('America/Fortaleza'))

    def test_date_only_and_missing_end(self):
        self.assertEqual(self.provider._convert_date(ICalGLib.Time.new_from_string('20261105')), '2026-11-05')
        self.assertIsNone(self.provider._convert_date(None))

    def test_utc_and_zoned_and_floating(self):
        utc = ICalGLib.Time.new_from_string('20261105T120000Z')
        self.assertEqual(self.provider._convert_date(utc), '2026-11-05T09:00:00-03:00')
        floating = ICalGLib.Time.new_from_string('20261105T120000')
        self.assertEqual(self.provider._convert_date(floating), '2026-11-05T12:00:00-03:00')
        floating.set_timezone(ICalGLib.Timezone.get_builtin_timezone('America/New_York'))
        self.assertEqual(self.provider._convert_date(floating), '2026-11-05T14:00:00-03:00')

    def test_discovery_and_selection(self):
        first, second, disabled = Mock(), Mock(), Mock()
        for source, uid, name in [(first, 'fake-a', 'A'), (second, 'fake-b', 'B'), (disabled, 'fake-c', 'C')]:
            source.get_uid.return_value = uid
            source.get_display_name.return_value = name
        registry = Mock()
        registry.list_sources.return_value = [second, disabled, first]
        registry.check_enabled.side_effect = lambda source: source is not disabled
        self.assertEqual(self.provider.list_calendars(registry), [first, second])
        with self.assertRaises(ValueError):
            self.provider._select_source(registry)
        self.provider.calendar_uid = 'fake-b'
        self.assertIs(self.provider._select_source(registry), second)
        self.provider.calendar_uid = 'fake-c'
        with self.assertRaises(ValueError):
            self.provider._select_source(registry)
        self.provider.calendar_uid = None
        registry.list_sources.return_value = [first]
        self.assertIs(self.provider._select_source(registry), first)
        registry.list_sources.return_value = []
        with self.assertRaises(ValueError):
            self.provider._select_source(registry)

    def test_instance_callback_preserves_dates_and_expands_window(self):
        import providers.evolution as module
        from unittest.mock import patch
        registry, client, component = Mock(), Mock(), Mock()
        component.get_summary.return_value = 'Evento sintético'
        def generate(start, end, cancellable, callback, data):
            callback(component, ICalGLib.Time.new_from_string('20261105'), ICalGLib.Time.new_from_string('20261107'))
        client.generate_instances_sync.side_effect = generate
        with patch.object(module.EDataServer.SourceRegistry, 'new_sync', return_value=registry), patch.object(self.provider, '_select_source'), patch.object(module.ECal.Client, 'connect_sync', return_value=client):
            start = datetime(2026, 11, 5, tzinfo=ZoneInfo('America/Fortaleza'))
            events = self.provider.get_events(start, start.replace(day=7))
        self.assertEqual(events, [CalendarEvent('Evento sintético', '2026-11-05', '2026-11-07', True)])
        self.assertEqual(client.generate_instances_sync.call_args.args[:2], (int(start.timestamp()), int(start.replace(day=7).timestamp())))
