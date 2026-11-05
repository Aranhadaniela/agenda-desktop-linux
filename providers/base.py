
from abc import ABC, abstractmethod
from datetime import datetime

from core.models import CalendarEvent


class CalendarProvider(ABC):

    @abstractmethod
    def get_events(
        self,
        start: datetime,
        end: datetime
    ) -> list[CalendarEvent]:
        """Retorna os eventos dentro do intervalo informado."""
        pass

