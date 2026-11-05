
from datetime import datetime, timezone

import gi

gi.require_version("EDataServer", "1.2")
gi.require_version("ECal", "2.0")
gi.require_version("ICalGLib", "3.0")

from gi.repository import EDataServer, ECal

from core.models import CalendarEvent
from core.timezones import local_timezone
from providers.base import CalendarProvider


class EvolutionProvider(CalendarProvider):

    def __init__(self, calendar_uid: str | None = None, *, tz=None):
        self.calendar_uid = calendar_uid
        self.tz = tz if tz is not None else local_timezone()

    @staticmethod
    def list_calendars(registry=None):
        """Return enabled calendar sources; never modify registry or sources."""
        if registry is None:
            registry = EDataServer.SourceRegistry.new_sync(None)
        return sorted(
            [source for source in registry.list_sources(EDataServer.SOURCE_EXTENSION_CALENDAR)
             if registry.check_enabled(source)],
            key=lambda source: (source.get_display_name().casefold(), source.get_uid())
        )

    def _select_source(self, registry):
        sources = self.list_calendars(registry)
        if self.calendar_uid:
            for source in sources:
                if source.get_uid() == self.calendar_uid:
                    return source
            raise ValueError('Calendário não encontrado ou desabilitado; use --list-calendars')
        if len(sources) == 1:
            return sources[0]
        if not sources:
            raise ValueError('Nenhum calendário habilitado disponível')
        raise ValueError('Há vários calendários; use --list-calendars e --calendar UID')

    def _convert_date(self, value):
        if value is None:
            return None

        all_day = bool(value.is_date())

        dt = datetime(
            value.get_year(),
            value.get_month(),
            value.get_day(),
            0 if all_day else value.get_hour(),
            0 if all_day else value.get_minute(),
            0 if all_day else value.get_second()
        )

        if all_day:
            return dt.date().isoformat()

        local_tz = self.tz

        if value.is_utc():
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            zone = value.get_timezone()

            if zone is not None:
                # libical resolves its own TZIDs, including vendor-prefixed IDs
                # and custom VTIMEZONE definitions unknown to zoneinfo.
                return datetime.fromtimestamp(value.as_timet_with_zone(zone), timezone.utc).astimezone(local_tz).isoformat()
            dt = dt.replace(tzinfo=local_tz)

        return dt.astimezone(local_tz).isoformat()

    def get_events(
        self,
        start: datetime,
        end: datetime
    ) -> list[CalendarEvent]:

        registry = EDataServer.SourceRegistry.new_sync(None)
        source = self._select_source(registry)

        client = ECal.Client.connect_sync(
            source,
            ECal.ClientSourceType.EVENTS,
            30,
            None
        )

        events = []

        def callback(component, event_start, event_end, *args):
            events.append(
                CalendarEvent(
                    title=component.get_summary() or "Sem título",
                    start=self._convert_date(event_start),
                    end=self._convert_date(event_end),
                    all_day=bool(event_start.is_date())
                )
            )
            return True

        client.generate_instances_sync(
            int(start.timestamp()),
            int(end.timestamp()),
            None,
            callback,
            None
        )

        return events

