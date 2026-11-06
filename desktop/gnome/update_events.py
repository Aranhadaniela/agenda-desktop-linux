"""Private GNOME adapter entry point. Bundled Core is copied by the installer."""
import configparser
import fcntl
import os
from pathlib import Path
import stat
import sys


def xdg_dir(variable, fallback):
    value = os.environ.get(variable, '')
    return Path(value) if value and Path(value).is_absolute() else Path.home() / fallback


def private_cache():
    directory = xdg_dir('XDG_CACHE_HOME', '.cache') / 'agenda-desktop-linux-gnome'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('Cache directory must be private and owned by user')
    return directory


def selection():
    path = xdg_dir('XDG_CONFIG_HOME', '.config') / 'agenda-desktop-linux' / 'gnome.ini'
    if not path.exists():
        return 'eds', os.environ.get('CALENDAR_UID') or None
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 65536:
        raise ValueError('Invalid private configuration')
    config = configparser.ConfigParser(interpolation=None)
    with path.open(encoding='utf-8') as stream:
        config.read_file(stream)
    source = config.get('calendar', 'source', fallback='eds').strip()
    if source not in {'eds', 'synthetic'}:
        raise ValueError('Unknown calendar source')
    uid = config.get('calendar', 'uid', fallback='').strip()
    if len(uid) > 4096 or any(ord(char) < 32 for char in uid):
        raise ValueError('Invalid calendar selection')
    return source, uid or None


def calendar_uid():
    return selection()[1]


class SyntheticProvider:
    """Opt-in local fixture; does not import GI or communicate with EDS."""
    def get_events(self, start, end):
        from datetime import timedelta
        from core.models import CalendarEvent
        today = start.date()
        tomorrow = today + timedelta(days=1)
        after = today + timedelta(days=2)
        return [
            CalendarEvent('Exemplo: dia inteiro', today.isoformat(), tomorrow.isoformat(), True),
            CalendarEvent('Exemplo: vários dias', today.isoformat(), after.isoformat(), True),
            CalendarEvent('Exemplo: reunião amanhã',
                          (start + timedelta(days=1, hours=10)).isoformat(),
                          (start + timedelta(days=1, hours=11)).isoformat()),
            CalendarEvent('Exemplo: título longo <b>texto literal</b> — acessibilidade e quebra de linha',
                          tomorrow.isoformat(), None, True),
        ]


def main():
    # Installed code is always relative to this adapter, never a shell/PATH lookup.
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
    cache = private_cache()
    descriptor = os.open(cache / 'update.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as lock:
        info = os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Invalid lock file')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 75
        from core.calendar_service import CalendarService
        from core.json_writer import write_events
        source, uid = selection()
        if source == 'synthetic':
            provider = SyntheticProvider()
        else:
            from providers.evolution import EvolutionProvider
            provider = EvolutionProvider(uid)
        events = CalendarService(provider).get_upcoming_events(days=2)
        write_events(events, cache / 'eventos.json')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        # Do not leak source names, titles, UIDs or library errors to Shell logs.
        print('Agenda: atualização indisponível; verifique dependências e seleção local.', file=sys.stderr)
        sys.exit(1)
