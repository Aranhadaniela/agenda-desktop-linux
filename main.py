
import argparse
import os
from pathlib import Path

from core.calendar_service import CalendarService
from core.json_writer import write_events
from providers.evolution import EvolutionProvider


def main():
    parser = argparse.ArgumentParser(
        description="Agenda Desktop Linux"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=2,
        help="Quantidade de dias a consultar"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("eventos.json"),
        help="Caminho do arquivo JSON"
    )

    parser.add_argument('--list-calendars', action='store_true', help='Lista calendários habilitados (contém identificadores locais)')
    parser.add_argument('--calendar', help='UID obtido com --list-calendars')
    args = parser.parse_args()

    if args.list_calendars:
        for source in EvolutionProvider.list_calendars():
            print(f"{source.get_uid()}\t{source.get_display_name()}")
        return

    calendar_uid = args.calendar or os.getenv("CALENDAR_UID")
    provider = EvolutionProvider(calendar_uid)
    service = CalendarService(provider)

    try:
        events = service.get_upcoming_events(days=args.days)
    except ValueError as error:
        parser.error(str(error))

    write_events(events, args.output)

    print(f"Eventos exportados: {len(events)}")
    print(f"Arquivo: {args.output.resolve()}")


if __name__ == "__main__":
    main()

