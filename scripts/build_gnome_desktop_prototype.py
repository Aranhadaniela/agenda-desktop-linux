"""Prepare the desktop-layer experiment. This script has no installation mode."""
import argparse
import hashlib
import json
import stat
from zipfile import ZipFile, ZipInfo, ZIP_STORED
from pathlib import Path
if __package__:
    from .install_gnome import ROOT, data_home
else:
    from install_gnome import ROOT, data_home

UUID = 'agenda-desktop-linux-desktop-prototype@extensions.local'
SOURCES = {
    'extension.js': 'desktop/gnome/prototype-desktop/extension.js',
    'desktopLayer.js': 'desktop/gnome/prototype-desktop/desktopLayer.js',
    'metadata.json': 'desktop/gnome/prototype-desktop/metadata.json',
    'events.js': 'desktop/gnome/events.js',
    'stylesheet.css': 'desktop/gnome/stylesheet.css',
    'LICENSE': 'LICENSE',
}


def validate_preparation_path(destination):
    destination = Path(destination)
    roots = (data_home() / 'gnome-shell/extensions', Path.home() / '.local/share/gnome-shell/extensions')
    if any(destination.resolve().is_relative_to(root.resolve()) for root in roots):
        raise ValueError('Preparation in extension directories is forbidden')


def build(destination):
    destination = Path(destination)
    validate_preparation_path(destination)
    destination.mkdir(mode=0o755, parents=True, exist_ok=False)
    for name, relative in SOURCES.items():
        source = ROOT / relative
        if source.is_symlink() or not source.is_file():
            raise ValueError('Invalid prototype source')
        with (destination / name).open('xb') as stream:
            stream.write(source.read_bytes())
        (destination / name).chmod(0o644)
    return destination


def create_archive(directory, archive):
    """Archive exactly the reviewed bytes, using fixed ZIP metadata."""
    directory, archive = Path(directory), Path(archive)
    validate_preparation_path(archive)
    if directory.is_symlink() or archive.resolve().is_relative_to(directory.resolve()):
        raise ValueError('Archive must be outside the six-file package')
    if {path.name for path in directory.iterdir()} != set(SOURCES):
        raise ValueError('Unexpected package content')
    contents = {}
    for name, relative in SOURCES.items():
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o777 != 0o644:
            raise ValueError('Invalid package file')
        contents[name] = path.read_bytes()
        if contents[name] != (ROOT / relative).read_bytes():
            raise ValueError('Package does not match current reviewed sources')
    metadata = json.loads(contents['metadata.json'])
    if metadata['uuid'] != UUID or metadata['shell-version'] != ['46']:
        raise ValueError('Invalid prototype metadata')
    with archive.open('xb') as stream:
        with ZipFile(stream, 'w', compression=ZIP_STORED) as bundle:
            for name in sorted(contents):
                info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                bundle.writestr(info, contents[name])
    return hashlib.sha256(archive.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/gnome-desktop-prototype' / UUID)
    parser.add_argument('--archive', type=Path, help='ZIP novo fora do diretório do pacote; exatamente seis arquivos')
    args = parser.parse_args()
    try:
        if args.archive:
            validate_preparation_path(args.archive)
            if args.archive.exists() or args.archive.is_symlink():
                raise ValueError('Archive already exists')
        build(args.output)
        if args.archive:
            digest = create_archive(args.output, args.archive)
            print(f'SHA256: {digest}')
    except (OSError, ValueError, KeyError):
        parser.error('Destino indisponível ou proibido; não sobrescrevemos arquivos existentes')
    print('Protótipo preparado; nada instalado ou ativado.')


if __name__ == '__main__':
    main()
