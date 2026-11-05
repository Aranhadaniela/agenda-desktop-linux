
import json
import os
import tempfile
from pathlib import Path

from core.models import CalendarEvent


def write_events(
    events: list[CalendarEvent],
    output: str | Path
) -> None:

    output = Path(output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "eventos": [
            {
                "titulo": event.title,
                "inicio": event.start,
                "fim": event.end,
                "dia_inteiro": event.all_day
            }
            for event in events
        ]
    }

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False
        ) as file:
            temporary_path = Path(file.name)
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_path, output)

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
