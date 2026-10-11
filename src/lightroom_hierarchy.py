"""Catalog bindings outside YAML and direct Lightroom hierarchy synchronization."""
import json
from pathlib import Path
import time
from urllib.parse import quote, unquote
import uuid

import yaml
from entry_identity import ensure_file_uuids

QUEUE = Path.home() / 'AppData' / 'Local' / 'BirdDeckTagging'


def state_path(config_path):
    return Path(config_path).with_suffix('.lightroom.json')


def entries(config):
    result = []
    def walk(entry, name, parent, path):
        full = (*path, name)
        if any(name.casefold() == ancestor.casefold() for ancestor in path):
            raise ValueError(f'Ancestor name conflict: {" > ".join(full)}')
        signature = (entry.get('scientific_name') or entry.get('icon') or '') if entry.get('type') == 'bird' else ''
        node = {'index': len(result) + 1, 'parent': parent, 'name': name, 'path': list(full),
                'type': entry.get('type', 'group'), 'title': entry.get('title', name), 'species': signature,
                'uuid': entry.get('uuid', '').lower(), 'id': ''}
        result.append(node)
        for child in entry.get('items', []):
            title = name + ' (?)' if child['type'] == 'uncertain' else child.get('tag', child['title'])
            walk(child, title, node['index'], full)
        node['descendants'] = sorted(n['species'] for n in result[node['index']:] if n['species'] and n['path'][:len(full)] == list(full))
    walk(config['profile'], 'Vogel', 0, ())
    paths = [tuple(p.casefold() for p in n['path']) for n in result]
    if len(paths) != len(set(paths)):
        raise ValueError('Duplicate keyword paths in config')
    return result


def bind_entries(config, state):
    desired = entries(config)
    old = state.get('entries', [])
    used = set()
    for node in desired:
        candidates = [n for n in old if node['uuid'] and n.get('uuid') == node['uuid']]
        # Name/species matching is only for migration of pre-UUID bindings.
        legacy = [n for n in old if not n.get('uuid')]
        if not candidates and node['species']:
            candidates = [n for n in legacy if n.get('species') == node['species'] and n['type'] == node['type']]
        if not candidates:
            candidates = [n for n in legacy if n['path'] == node['path']]
        if not candidates:
            candidates = [n for n in legacy if n['type'] == node['type'] and n['title'] == node['title']]
        if not candidates and node['type'] == 'group' and node['descendants']:
            candidates = [n for n in legacy if n['type'] == 'group' and n.get('descendants') == node['descendants']]
        candidates = [n for n in candidates if n['id'] not in used]
        if len(candidates) > 1:
            raise ValueError(f'Ambiguous saved binding for {node["name"]}')
        if candidates:
            node['id'] = candidates[0]['id']
        if node['id']:
            if node['id'] in used:
                raise ValueError('Catalog ID matched twice')
            used.add(node['id'])
    return desired


def catalog_key(catalog):
    return catalog.replace('\\', '/').lower()


def load_states(config_path):
    path = state_path(config_path)
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if data.get('version') == 2:
        return data['catalogs']
    return {catalog_key(data['catalog']): data} if data else {}


def load_state(config_path, catalog=None):
    states = load_states(config_path)
    return states.get(catalog_key(catalog), {}) if catalog is not None else next(iter(states.values()), {})


def attach_bindings(config, config_path):
    def walk(items):
        for item in items:
            item['_keyword_uuid'] = item.get('uuid', '').lower()
            walk(item.get('items', []))
    walk(config['profile']['items'])


def exchange(mode, catalog='', body='', timeout=120):
    QUEUE.mkdir(parents=True, exist_ok=True)
    identity = uuid.uuid4().hex
    request = QUEUE / (identity + '.request')
    response = QUEUE / (identity + '.response')
    staging = request.with_suffix('.tmp')
    staging.write_text(f'HIERARCHY\n{int(time.time()) + timeout}\n{mode}\n{quote(catalog, safe="")}\n{body}', encoding='utf-8', newline='\n')
    staging.replace(request)
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if response.exists():
                text = response.read_text(encoding='utf-8')
                if not text.startswith('OK\t'):
                    raise ValueError(text.removeprefix('ERROR\t'))
                return text
            time.sleep(.1)
        raise TimeoutError('Lightroom did not respond; reload BirdDeck Tagging')
    finally:
        request.unlink(missing_ok=True)
        response.unlink(missing_ok=True)


def snapshot():
    text = exchange('SNAPSHOT')
    version, catalog, *rows = text.splitlines()
    if version != 'OK\tSNAPSHOT\tINCREMENTAL-2':
        raise ValueError('Lightroom is running an older hierarchy updater. Reload BirdDeck Tagging, then use Start / Restart BirdDeck Tagging before syncing.')
    nodes = []
    for row in rows:
        if not row:
            continue
        identity, parent, name, photos = row.split('\t')
        nodes.append({'id': identity, 'parent_id': parent, 'name': unquote(name), 'photos': int(photos)})
    by_id = {n['id']: n for n in nodes}
    for node in nodes:
        path, current, seen = [], node, set()
        while current:
            if current['id'] in seen:
                raise ValueError('Catalog hierarchy cycle')
            seen.add(current['id'])
            path.insert(0, current['name'])
            current = by_id.get(current['parent_id'])
        node['path'] = path
    return unquote(catalog), nodes, ('\n'.join(rows).rstrip('\n') + '\n') if rows else ''


def make_plan(config, state, catalog, live):
    if state.get('catalog', catalog).replace('\\', '/').casefold() != catalog.replace('\\', '/').casefold():
        raise ValueError('Open catalog differs from saved bindings')
    desired = bind_entries(config, state)
    scoped = [n for n in live if n['path'][0] == 'Vogel']
    # Saved UUID bindings prove ownership even after an interrupted move leaves
    # a keyword outside Vogel. Unbound name matching remains inside Vogel.
    by_id = {n['id']: n for n in live}
    used = set()
    changes = []
    for node in desired:
        if node['id'] and node['id'] not in by_id:
            raise ValueError(f'Saved keyword missing from catalog: {node["name"]}')
        match = by_id.get(node['id'])
        if not match:
            candidates = [n for n in scoped if n['path'] == node['path'] and n['id'] not in used]
            if not candidates:
                candidates = [n for n in scoped if n['name'] == node['name'] and n['id'] not in used]
            if len(candidates) > 1:
                raise ValueError(f'Ambiguous catalog match: {node["name"]}')
            match = candidates[0] if candidates else None
        if node['type'] == 'bird' and (not match or match['photos'] == 0):
            populated = [n for n in scoped if n['name'] == node['name'] and n['photos'] > 0 and n['id'] not in used]
            if len(populated) > 1:
                raise ValueError(f'Multiple populated keywords: {node["name"]}')
            if populated:
                match = populated[0]
        if match:
            node['id'] = match['id']
            if node['id'] in used:
                raise ValueError('Keyword matched twice')
            used.add(node['id'])
            if match['path'] != node['path']:
                changes.append('Move/rename: ' + ' > '.join(match['path']) + ' -> ' + ' > '.join(node['path']))
        else:
            changes.append('Create: ' + ' > '.join(node['path']))
    for node in scoped:
        if node['id'] not in used:
            changes.append(f'Archive: {" > ".join(node["path"])} ({node["photos"]} photos)')
    return desired, changes


def sync(config_path, apply=False):
    config_path = Path(config_path)
    config = ensure_file_uuids(config_path)
    catalog, live, fingerprint = snapshot()
    state = load_state(config_path, catalog)
    desired, changes = make_plan(config, state, catalog, live)
    print('\n'.join(changes) if changes else 'Hierarchy already matches config.')
    print(f'{len(changes)} changes; {len(desired)} desired keywords.')
    if changes and not apply:
        print('Preview only. Run again with --apply to synchronize.')
        return
    if changes:
        rows = ''.join(f'{n["index"]}\t{n["parent"]}\t{n["id"] or "0"}\t{quote(n["name"], safe="")}\n' for n in desired)
        result = exchange('APPLY', catalog, 'EXPECTED\n' + fingerprint + 'NODES\n' + rows, timeout=600)
        assigned = dict(line.split('\t') for line in result.splitlines()[1:] if line)
        for node in desired:
            node['id'] = assigned[str(node['index'])]
        # Persist new IDs before verification so a later interrupted request is recoverable.
        save_state(config_path, catalog, desired)
        actual_catalog, actual, _ = snapshot()
        if actual_catalog != catalog:
            raise ValueError('Catalog changed during verification')
        expected = {n['id']: n['path'] for n in desired}
        current = {n['id']: n['path'] for n in actual if n['path'][0] == 'Vogel'}
        if expected != current:
            raise ValueError('Post-sync hierarchy verification failed')
        counts = {n['id']: n['photos'] for n in actual}
        if any(counts.get(n['id']) != n['photos'] for n in live if n['photos']):
            raise ValueError('Post-sync photo-assignment verification failed')
    save_state(config_path, catalog, desired)
    publish_bindings(config_path)
    print(f'Bindings saved: {state_path(config_path)}')


def save_state(config_path, catalog, desired):
    states = load_states(config_path)
    states[catalog_key(catalog)] = {'catalog': catalog, 'entries': desired}
    data = {'version': 2, 'catalogs': states}
    target = state_path(config_path)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(target)


def publish_bindings(config_path):
    """Publish UUID resolution for every known catalog to the Lightroom listener."""
    QUEUE.mkdir(parents=True, exist_ok=True)
    target = QUEUE / 'keyword-bindings.tsv'
    mappings = {}
    if target.exists():
        for row in target.read_text(encoding='utf-8').splitlines():
            catalog, identity, keyword = row.split('\t')
            mappings[(catalog, identity)] = keyword
    for state in load_states(config_path).values():
        catalog = quote(catalog_key(state['catalog']), safe='')
        for node in state['entries']:
            if node.get('uuid') and node['id']:
                mappings[(catalog, node['uuid'])] = node['id']
    temporary = target.with_suffix('.tmp')
    temporary.write_text(''.join(f'{c}\t{u}\t{k}\n' for (c, u), k in sorted(mappings.items())), encoding='utf-8', newline='\n')
    temporary.replace(target)
