"""Synchronize Vogel to YAML while preserving identities with assigned photos."""
import csv
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

HEADER = ['Id', '# Photos', 'Include on Export', 'Export Containing Keywords',
          'Export Synonyms', 'Person', 'Synonym', 'Level']


def read_catalog(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        rows = list(csv.reader(handle))
    if len(rows) < 2 or rows[0] != HEADER or not rows[1][0]:
        raise ValueError('Expected an Any Tag Export Keywords CSV with its catalog path')
    nodes, stack, ids = [], [], set()
    for row in rows[2:]:
        if not any(row):
            continue
        if len(row) < 9 or row[6] not in ('Y', 'N'):
            raise ValueError('Invalid Any Tag keyword row')
        # The last nonempty cell is the informational parent path (except at root).
        column = next((i for i in range(8, len(row)) if row[i]), None)
        if column is None:
            raise ValueError('Keyword row has no name')
        depth = column - 8
        if depth > len(stack):
            raise ValueError('Keyword hierarchy skips a parent')
        stack = stack[:depth]
        parent = stack[-1] if stack else None
        if row[6] == 'Y' and parent is None:
            raise ValueError('Synonym has no keyword parent')
        node = dict(name=row[column], parent=parent, attrs=row[:8], children=[],
                    path=(*parent['path'], row[column]) if parent else (row[column],))
        if row[0]:
            if row[0] in ids:
                raise ValueError(f'Duplicate keyword ID: {row[0]}')
            ids.add(row[0])
        nodes.append(node)
        if parent:
            parent['children'].append(node)
        stack.append(node)
    return rows[:2], nodes


def generate_anytag(config_path, catalog_path, destination, bind=False):
    config_path, destination = Path(config_path), Path(destination)
    if destination.resolve() in (config_path.resolve(), Path(catalog_path).resolve()):
        raise ValueError('Output must be separate from the config and catalog export')
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    config = yaml.load(config_path.read_text(encoding='utf-8-sig'))
    preamble, original = read_catalog(catalog_path)
    profile = config['profile']
    catalog = preamble[1][0]
    if profile.get('anytag_catalog', catalog) != catalog:
        raise ValueError('Export belongs to a different Lightroom catalog')
    keywords = [n for n in original if n['attrs'][6] == 'N']
    scoped = [n for n in keywords if n['path'][0] == 'Vogel']
    by_id = {n['attrs'][0]: n for n in keywords if n['attrs'][0]}
    used, bindings = set(), []
    desired = []

    def walk(entry, name, parent, path):
        identity = str(entry.get('anytag_id', ''))
        match = by_id.get(identity) if identity else None
        if identity and match is None:
            raise ValueError(f'Keyword ID {identity} missing from export: {name}')
        if match and match not in scoped:
            raise ValueError(f'Keyword ID {identity} is outside Vogel: {name}')
        if not identity:
            candidates = [n for n in scoped if n['path'] == path]
            if not candidates:
                candidates = [n for n in scoped if n['name'] == name]
            if not candidates:
                candidates = [n for n in scoped if n['name'].replace('-', '').casefold() == name.replace('-', '').casefold()]
            populated = [n for n in candidates if int(n['attrs'][1]) > 0]
            if len(populated) == 1 and entry.get('type') != 'group':
                candidates = populated
            if len(candidates) > 1:
                choices = ', '.join(f"{n['attrs'][0]} ({' > '.join(n['path'])})" for n in candidates)
                raise ValueError(f'Ambiguous keyword {name}; set anytag_id in YAML: {choices}')
            match = candidates[0] if candidates else None
        # A former flat bird may now have a group with the same name. Reserve
        # the populated identity for the bird, and create its new group.
        if (entry.get('type') == 'group' and match and int(match['attrs'][1]) > 0
                and any(c.get('type') != 'group' and c.get('tag', c.get('title')) == name
                        for c in entry.get('items', []))):
            match = None
        if entry.get('type') != 'group' and (match is None or int(match['attrs'][1]) == 0):
            populated = [n for n in scoped if n['name'].replace('-', '').casefold() == name.replace('-', '').casefold()
                         and int(n['attrs'][1]) > 0 and id(n) not in used]
            if len(populated) > 1:
                raise ValueError(f'Multiple populated keywords for {name}; merge their photo assignments in Lightroom first')
            if populated:
                match = populated[0]
        if match and id(match) in used:
            raise ValueError(f'Catalog keyword matched twice: {name}')
        if match:
            used.add(id(match))
        bindings.append((entry, match['attrs'][0] if match else None))
        node = dict(name=name, parent=parent, children=[],
                    attrs=list(match['attrs']) if match else ['', '0', 'Y', 'Y', 'Y', 'N', 'N', ''])
        desired.append((node, match))
        if parent:
            parent['children'].append(node)
        for child in entry.get('items', []):
            title = name + ' (?)' if child['type'] == 'uncertain' else child.get('tag', child['title'])
            walk(child, title, node, (*path, title))
        return node

    root = walk(profile, 'Vogel', None, ('Vogel',))
    replacements = {id(match): node for node, match in desired if match}
    # Vogel is authoritative. Omitted IDs are handled by Any Tag's deletion
    # option; keep all other roots and synonyms of the selected identities.
    retained = {id(n): dict(name=n['name'], attrs=list(n['attrs']), children=[], parent=None)
                for n in original if id(n) not in used and
                (n['path'][0] != 'Vogel' or
                 (n['attrs'][6] == 'Y' and id(n['parent']) in used))}
    all_nodes = {**retained, **replacements}
    roots = [root]
    for old in original:
        if id(old) not in retained:
            continue
        node = retained[id(old)]
        parent = all_nodes.get(id(old['parent'])) if old['parent'] else None
        node['parent'] = parent
        if parent:
            parent['children'].append(node)
        else:
            roots.append(node)
    rows = list(preamble)

    def emit(node, ancestors):
        attrs = list(node['attrs'])
        attrs[7] = str(len(ancestors) + 1)
        row = attrs + [''] * len(ancestors) + [node['name']]
        if ancestors:
            row.append(' < '.join(reversed(ancestors)))
        rows.append(row)
        # Synonyms must immediately follow their keyword, before child keywords.
        for child in sorted(node['children'], key=lambda n: n['attrs'][6] != 'Y'):
            emit(child, [*ancestors, node['name']])

    for node in roots:
        emit(node, [])
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('w', encoding='utf-8-sig', newline='') as handle:
        csv.writer(handle).writerows(rows)
    if bind:
        for entry, identity in bindings:
            if identity:
                entry['anytag_id'] = identity
            else:
                entry.pop('anytag_id', None)
        profile['anytag_catalog'] = catalog
        buffer = StringIO()
        yaml.dump(config, buffer)
        config_path.write_text(buffer.getvalue(), encoding='utf-8')
    return destination
