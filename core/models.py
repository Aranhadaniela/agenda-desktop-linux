
from dataclasses import dataclass


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    start: str
    end: str | None
    all_day: bool = False
