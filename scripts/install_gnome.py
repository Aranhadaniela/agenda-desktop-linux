"""Build a GNOME package; installation is opt-in and never replaces a directory."""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
UUID = 'agenda-desktop-linux@extensions.local'
EXTENSION_FILES = ('extension.js', 'events.js', 'metadata.json', 'stylesheet.css', 'update_events.py')
CORE_FILES = (
    'core/__init__.py', 'core/models.py', 'core/calendar_service.py',
    'core/json_writer.py', 'core/timezones.py',
    'providers/__init__.py', 'providers/base.py', 'providers/evolution.py',
)


def data_home():
    value = os.environ.get('XDG_DATA_HOME', '')
    return Path(value) if value and Path(value).is_absolute() else Path.home() / '.local/share'


def build(destination):
    destination = Path(destination)
    # Exclusive creation: never merge with or overwrite an existing extension.
    destination.mkdir(mode=0o755, parents=True, exist_ok=False)
    pairs = [(ROOT / 'desktop/gnome' / name, destination / name) for name in EXTENSION_FILES]
    pairs += [(ROOT / name, destination / 'python' / name) for name in CORE_FILES]
    pairs += [(ROOT / 'LICENSE', destination / 'LICENSE')]
    for source, target in pairs:
        if source.is_symlink() or not source.is_file():
            raise ValueError('Invalid package source')
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive output prevents overwriting a file introduced concurrently.
        with source.open('rb') as reader, target.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
        target.chmod(0o644)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--output', type=Path, help='Diretório novo para preparar o pacote (não instala)')
    mode.add_argument('--install', action='store_true', help='Instala somente após confirmação; não ativa')
    args = parser.parse_args()
    if args.install:
        destination = data_home() / 'gnome-shell/extensions' / UUID
        if os.path.lexists(destination):
            parser.error('Destino já existe; substituição não é suportada. Nada foi alterado.')
        if not sys.stdin.isatty():
            parser.error('Instalação exige confirmação em terminal interativo')
        print('Instalar uma NOVA extensão e seu Core no diretório de extensões do usuário?')
        if input(f'Digite {UUID} para confirmar: ').strip() != UUID:
            parser.error('Instalação cancelada')
    else:
        destination = args.output or ROOT / 'dist/gnome' / UUID
        # Preparation must not serve as a back door to installation.
        extension_roots = [data_home() / 'gnome-shell/extensions', Path.home() / '.local/share/gnome-shell/extensions']
        if any(destination.resolve().is_relative_to(root.resolve()) for root in extension_roots):
            parser.error('Use --install para um destino de extensões; confirmação obrigatória')
    try:
        build(destination)
    except (OSError, ValueError):
        parser.error('Não foi possível preparar pacote; destino pode estar incompleto. Nenhum arquivo existente foi substituído.')
    print('Pacote preparado. Nenhuma extensão foi ativada.')


if __name__ == '__main__':
    main()
