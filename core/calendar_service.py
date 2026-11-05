from datetime import datetime, timedelta, timezone

from core.models import CalendarEvent
from core.timezones import local_timezone
from providers.base import CalendarProvider


class CalendarService:
    def __init__(self, provider: CalendarProvider, *, tz=None, clock=None):
        self.provider = provider
        self.tz = tz if tz is not None else local_timezone()
        self.clock = clock if clock is not None else lambda: datetime.now(self.tz)

    def get_upcoming_events(self, days: int = 2) -> list[CalendarEvent]:
        if days < 1:
            raise ValueError('days deve ser maior que zero')
        now = self.clock().astimezone(self.tz)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=days)
        events = self.provider.get_events(start, end)

        def instant(event):
            value = datetime.fromisoformat(event.start)
            if value.tzinfo is None:
                value = value.replace(tzinfo=self.tz)
            return value.astimezone(timezone.utc)

        return sorted(events, key=instant)
