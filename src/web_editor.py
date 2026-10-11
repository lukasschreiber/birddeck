"""Local browser editor with atomic, comment-preserving YAML saves."""
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO, BytesIO
import json
import os
from pathlib import Path
import secrets
import mimetypes
import subprocess
from tempfile import NamedTemporaryFile
from threading import Lock
import webbrowser
from urllib.parse import urlsplit, parse_qs

from ruamel.yaml import YAML
from config_validation import load_icons, validate_icons
from paths import ROOT_DIR


def render_preview(entry, icons):
    from gen_image import generate_image
    kind = entry.get('type')
    if kind not in ('bird', 'group', 'uncertain'):
        raise ValueError('Invalid entry type')
    icon = entry.get('icon', '').strip() if kind != 'uncertain' else ''
    if icon and icon not in icons:
        raise ValueError('Unknown icon ID')
    background = entry.get('bg') or entry.get('color') or '#ffffff'
    if kind == 'bird':
        background = entry.get('color') or '#ffffff'
    if kind == 'uncertain':
        background = str(ROOT_DIR / 'assets' / 'img' / 'unknown-bird.png')
    if not background.startswith('#'):
        image_path = (ROOT_DIR / background).resolve()
        if not image_path.is_relative_to((ROOT_DIR / 'assets').resolve()):
            raise ValueError('Preview background must be inside assets/')
    image = generate_image(icon, background, (288, 288), favorite=entry.get('favorite', False), exotic=entry.get('exotic', False))
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def preview_title(entry, parent_title):
    from gen_action import generate_folder_action, generate_bird_action, FolderType
    kind = entry['type']
    if kind == 'group':
        action = generate_folder_action('', FolderType.TAXA if entry.get('icon') else FolderType.MAIN, '', entry.get('title', ''))
    else:
        name = parent_title + ' (?)' if kind == 'uncertain' else entry.get('title', '')
        action = generate_bird_action(name, '', '', uncertain=kind == 'uncertain')
    state = action['States'][0]
    return {key: state[key] for key in ('Title', 'TitleAlignment', 'FontSize', 'TitleColor', 'OutlineThickness')}


class ConfigStore:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.allow_unicode = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        self.original = self.path.read_bytes()
        self.config = self.yaml.load(self.original.decode('utf-8-sig'))
        self.icons = load_icons()
        self.revision = 0
        self.lock = Lock()

    def snapshot(self):
        return {'config': self.config, 'revision': self.revision, 'file': str(self.path)}

    @staticmethod
    def entry_at(config, path):
        if not isinstance(path, list) or any(type(i) is not int or i < 0 for i in path):
            raise ValueError('Invalid entry path')
        entry = config['profile']
        for index in path:
            entry = entry['items'][index]
        return entry

    def save(self, request):
        with self.lock:
            if request.get('revision') != self.revision or self.path.read_bytes() != self.original:
                raise ValueError('Configuration changed. Reload the editor before saving.')
            candidate = deepcopy(self.config)
            path = request['path']
            adding = request.get('action') == 'add'
            if request.get('action') not in ('add', 'update'):
                raise ValueError('Unknown action')
            if not adding and not path:
                raise ValueError('Select an entry to update')
            target = self.entry_at(candidate, path)
            values = request['entry']
            kind = values.get('type')
            if kind not in ('bird', 'group', 'uncertain'):
                raise ValueError('Invalid entry type')
            if adding and target.get('type', 'group') != 'group':
                raise ValueError('Select a group to add a child')
            if not adding and kind != target['type']:
                raise ValueError('Existing entry types cannot be changed')
            item = {} if adding else target
            item['type'] = kind
            if kind != 'uncertain':
                title = values.get('title', '').strip()
                if not title:
                    raise ValueError('A title is required')
                item['title'] = title
                icon = values.get('icon', '').strip()
                if (kind == 'bird' and not icon) or (icon and icon not in self.icons):
                    raise ValueError('Choose an icon ID from data/icons.json')
                if icon:
                    item['icon'] = icon
                else:
                    item.pop('icon', None)
                for field in ('favorite', 'exotic'):
                    if values.get(field) is True:
                        item[field] = True
                    else:
                        item.pop(field, None)
            if kind == 'group':
                item.setdefault('items', [])
                for field in ('tag', 'bg'):
                    value = values.get(field, '').strip()
                    if value:
                        item[field] = value
                    else:
                        item.pop(field, None)
            selected = path
            if adding:
                selected = [*path, len(target['items'])]
                target['items'].append(item)
            validate_icons(candidate, self.icons)
            stream = StringIO()
            self.yaml.dump(candidate, stream)
            content = stream.getvalue().encode('utf-8')
            temporary = None
            try:
                with NamedTemporaryFile(dir=self.path.parent, delete=False) as file:
                    temporary = Path(file.name)
                    file.write(content)
                os.replace(temporary, self.path)
            finally:
                if temporary and temporary.exists():
                    temporary.unlink()
            self.config = candidate
            self.original = content
            self.revision += 1
            return {**self.snapshot(), 'selected': selected}


def make_server(config_path, port=0):
    store = ConfigStore(config_path)
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, status, body, content_type='application/json', extra_headers=None):
            data = json.dumps(body, ensure_ascii=False).encode('utf-8') if content_type == 'application/json' else body
            self.send_response(status)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            for name, value in (extra_headers or {}).items():
                self.send_header(name, value)
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def authorized(self):
            return secrets.compare_digest(self.headers.get('X-BirdDeck-Token', ''), token)

        def do_GET(self):
            parsed = urlsplit(self.path)
            route = parsed.path
            if route == '/api/backgrounds':
                if not self.authorized():
                    self.respond(403, {'error': 'Unauthorized'})
                    return
                self.respond(200, [path.relative_to(ROOT_DIR).as_posix() for path in sorted((ROOT_DIR / 'assets' / 'img').glob('*')) if path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp')])
                return
            if route in ('/api/icon-image', '/api/background-image'):
                query = parse_qs(parsed.query)
                if not secrets.compare_digest(query.get('token', [''])[0], token):
                    self.respond(403, {'error': 'Unauthorized'})
                    return
                if route == '/api/icon-image':
                    code = query.get('id', [''])[0]
                    if code not in store.icons:
                        self.respond(404, {'error': 'Unknown icon'})
                        return
                    asset = ROOT_DIR / '.cache' / 'icons' / f'{code}.jpg'
                    if not asset.exists():
                        import requests
                        try:
                            response = requests.get(f'https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{store.icons[code]}/640', timeout=15)
                            response.raise_for_status()
                            self.respond(200, response.content, 'image/jpeg')
                        except requests.RequestException:
                            self.respond(502, {'error': 'Icon download failed'})
                        return
                else:
                    asset = (ROOT_DIR / query.get('path', [''])[0]).resolve()
                    if not asset.is_relative_to((ROOT_DIR / 'assets' / 'img').resolve()):
                        self.respond(400, {'error': 'Invalid background path'})
                        return
                if asset.is_file():
                    mime = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}.get(asset.suffix.lower())
                    if mime:
                        self.respond(200, asset.read_bytes(), mime)
                        return
                self.respond(404, {'error': 'Image not found'})
                return
            if route in ('/api/config', '/api/icons'):
                if not self.authorized():
                    self.respond(403, {'error': 'Unauthorized'})
                    return
                with store.lock:
                    self.respond(200, store.snapshot() if route == '/api/config' else store.icons)
            else:
                directory = (ROOT_DIR / 'web' / 'dist').resolve()
                asset = (directory / ('index.html' if route == '/' else route.lstrip('/'))).resolve()
                if asset.is_relative_to(directory) and asset.is_file():
                    # Windows registry MIME mappings vary between user accounts.
                    mime = {
                        '.js': 'text/javascript', '.mjs': 'text/javascript',
                        '.css': 'text/css', '.html': 'text/html',
                        '.woff': 'font/woff', '.woff2': 'font/woff2',
                        '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
                    }.get(asset.suffix.lower()) or mimetypes.guess_type(asset.name)[0] or 'application/octet-stream'
                    self.respond(200, asset.read_bytes(), mime)
                else:
                    self.respond(404, {'error': 'Not found'})

        def do_POST(self):
            if not self.authorized():
                self.respond(403, {'error': 'Unauthorized'})
                return
            if self.path not in ('/api/entry', '/api/preview'):
                self.respond(404, {'error': 'Not found'})
                return
            try:
                length = int(self.headers.get('Content-Length', 0))
                if not 0 < length <= 65536:
                    raise ValueError('Invalid request size')
                request = json.loads(self.rfile.read(length))
                if self.path == '/api/preview':
                    title = preview_title(request['entry'], request.get('parentTitle', 'Vogel'))
                    self.respond(200, render_preview(request['entry'], store.icons), 'image/png',
                                 {'X-BirdDeck-Title': json.dumps(title, ensure_ascii=True)})
                    return
                result = store.save(request)
                self.respond(200, result)
            except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError) as error:
                self.respond(400, {'error': str(error)})

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    return server, token


def run_editor(config_path, port=0, open_browser=True):
    web_dir = ROOT_DIR / 'web'
    bundle = web_dir / 'dist' / 'index.html'
    sources = [web_dir / 'index.html', web_dir / 'package.json', web_dir / 'package-lock.json', *web_dir.glob('src/**/*')]
    if not bundle.exists() or any(path.is_file() and path.stat().st_mtime > bundle.stat().st_mtime for path in sources):
        npm = 'npm.cmd' if os.name == 'nt' else 'npm'
        if not (web_dir / 'node_modules').exists():
            subprocess.run([npm, 'ci'], cwd=web_dir, check=True)
        subprocess.run([npm, 'run', 'build'], cwd=web_dir, check=True)
    server, token = make_server(config_path, port)
    url = f'http://127.0.0.1:{server.server_port}/#{token}'
    print(f'BirdDeck editor: {url}', flush=True)
    print('Press Ctrl+C to stop the editor.', flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
