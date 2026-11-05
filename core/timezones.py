"""Local timezone with transition rules, without third-party dependencies."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def local_timezone():
    name = os.environ.get('TZ')
    if name:
        name = name.removeprefix(':')
        if name.startswith('/'):
            with open(name, 'rb') as stream:
                return ZoneInfo.from_file(stream)
        return ZoneInfo(name)
    try:
        with open('/etc/localtime', 'rb') as stream:
            return ZoneInfo.from_file(stream)
    except (OSError, ValueError):
        return datetime.now().astimezone().tzinfo
