"""Permanent, catalog-independent identities for configuration entries."""
from io import StringIO
from pathlib import Path
import os
from tempfile import NamedTemporaryFile
from uuid import UUID, uuid4

from ruamel.yaml import YAML


def walk_entries(config):
    def walk(item):
        yield item
        for child in item.get('items', []):
            yield from walk(child)
    yield from walk(config['profile'])


def ensure_uuids(config):
    seen = set()
    changed = False
    for item in walk_entries(config):
        if 'uuid' not in item:
            item['uuid'] = str(uuid4())
            changed = True
        try:
            identity = str(UUID(item['uuid']))
        except (ValueError, TypeError, AttributeError):
            raise ValueError(f'Invalid entry UUID: {item.get("uuid")}') from None
        if identity in seen:
            raise ValueError(f'Duplicate entry UUID: {identity}; copied entries need a new UUID')
        seen.add(identity)
        if item['uuid'] != identity:
            item['uuid'] = identity
            changed = True
    return changed


def ensure_file_uuids(path):
    path = Path(path)
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.allow_unicode = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    original = path.read_bytes()
    config = yaml.load(original.decode('utf-8-sig'))
    if ensure_uuids(config):
        stream = StringIO()
        yaml.dump(config, stream)
        temporary = None
        try:
            with NamedTemporaryFile(dir=path.parent, delete=False) as file:
                temporary = Path(file.name)
                file.write(stream.getvalue().encode('utf-8'))
            if path.read_bytes() != original:
                raise ValueError('Configuration changed while assigning UUIDs; retry')
            os.replace(temporary, path)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
    return config
