import json
from pathlib import Path
import sys
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from web_editor import make_server


class WebEditorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'config.yaml'
        self.path.write_text('# preserve comment\nprofile:\n  name: BirdDeck\n  items:\n'
                             '    - type: group\n      title: Vögel\n      items:\n'
                             '        - type: bird\n          title: Grünfink\n          icon: eurgre1\n', encoding='utf-8')
        self.server, self.token = make_server(self.path)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def request(self, route, data=None, token=True):
        request = Request(self.url + route, data=json.dumps(data).encode() if data else None,
                          headers={'X-BirdDeck-Token': self.token if token else ''})
        with urlopen(request) as response:
            return json.load(response)

    def test_add_update_validation_and_conflicts(self):
        self.assertEqual(self.request('/api/config')['revision'], 0)
        body = {'revision': 0, 'action': 'update', 'path': [0, 0],
                'entry': {'type': 'bird', 'title': 'Grünfink updated', 'icon': 'invalid'}}
        original = self.path.read_bytes()
        with self.assertRaises(HTTPError):
            self.request('/api/entry', body)
        self.assertEqual(self.path.read_bytes(), original)
        body['entry']['icon'] = 'eurgre1'
        self.assertEqual(self.request('/api/entry', body)['revision'], 1)
        self.assertIn('Grünfink updated', self.path.read_text(encoding='utf-8'))
        self.assertIn('# preserve comment', self.path.read_text(encoding='utf-8'))
        with self.assertRaises(HTTPError):
            self.request('/api/entry', body)
        body.update(revision=1, action='add', path=[0], entry={'type':'bird','title':'Amsel','icon':'eurbla'})
        result = self.request('/api/entry', body)
        self.assertEqual(len(result['config']['profile']['items'][0]['items']), 2)
        self.path.write_bytes(self.path.read_bytes() + b'# external\n')
        body['revision'] = 2
        before = self.path.read_bytes()
        with self.assertRaises(HTTPError):
            self.request('/api/entry', body)
        self.assertEqual(before, self.path.read_bytes())

    def test_static_assets_and_access_control(self):
        routes = ['/']
        web_dist = Path(__file__).resolve().parents[1] / 'web' / 'dist'
        routes.extend('/' + str(path.relative_to(web_dist)).replace('\\', '/') for path in (web_dist / 'assets').glob('*.js'))
        for route in routes:
            with urlopen(self.url + route) as response:
                self.assertEqual(response.status, 200)
                self.assertTrue(response.read())
        with self.assertRaises(HTTPError) as error:
            self.request('/api/config', token=False)
        self.assertEqual(error.exception.code, 403)
        self.assertIn('eurbla', self.request('/api/icons'))

    def test_asset_mime_types_override_windows_registry(self):
        from unittest.mock import patch
        directory = Path(__file__).resolve().parents[1] / 'web' / 'dist'
        assets = list((directory / 'assets').glob('*.js')) + list((directory / 'assets').glob('*.woff2'))[:1]
        self.assertGreaterEqual(len(assets), 2)
        with patch('web_editor.mimetypes.guess_type', return_value=('text/plain', None)):
            for asset in assets:
                route = '/' + asset.relative_to(directory).as_posix()
                with urlopen(self.url + route) as response:
                    expected = 'text/javascript' if asset.suffix == '.js' else 'font/woff2'
                    self.assertEqual(response.headers.get_content_type(), expected)
                    self.assertIn("font-src 'self' data:", response.headers['Content-Security-Policy'])
        with urlopen(self.url + '/favicon.svg') as response:
            self.assertEqual(response.headers.get_content_type(), 'image/svg+xml')

    def test_preview_returns_image_without_saving(self):
        from io import BytesIO
        from PIL import Image
        before = self.path.read_bytes()
        body = json.dumps({'entry': {'type': 'group', 'title': 'Preview', 'bg': '#abcdef'}}).encode()
        request = Request(self.url + '/api/preview', data=body, headers={'X-BirdDeck-Token': self.token})
        with urlopen(request) as response:
            self.assertEqual(response.headers.get_content_type(), 'image/png')
            image = Image.open(BytesIO(response.read()))
            self.assertEqual(image.size, (288, 288))
            self.assertEqual(image.getpixel((144, 144)), (171, 205, 239))
        self.assertEqual(before, self.path.read_bytes())
        with self.assertRaises(HTTPError):
            self.request('/api/preview', {'entry': {'type': 'bird', 'icon': 'invalid'}})

    def test_preview_title_matches_export_actions(self):
        from web_editor import preview_title
        cases = [
            ({'type': 'bird', 'title': 'Rotdrossel'}, '        Rot', 'top'),
            ({'type': 'group', 'title': 'Drossel', 'icon': 'redwin'}, '      [Dro]', 'top'),
            ({'type': 'group', 'title': 'Sing-vögel'}, 'Sing\nvögel', 'middle'),
            ({'type': 'uncertain'}, 'Drosse...', 'bottom'),
        ]
        for entry, title, alignment in cases:
            settings = preview_title(entry, 'Drossel')
            self.assertEqual(settings['Title'], title)
            self.assertEqual(settings['TitleAlignment'], alignment)
            self.assertEqual(settings['FontSize'], 9)

    def test_selector_images_and_backgrounds(self):
        from urllib.parse import urlencode
        backgrounds = self.request('/api/backgrounds')
        self.assertIn('assets/img/unknown-bird.png', backgrounds)
        for route, parameters, mime in [
            ('/api/background-image', {'path': 'assets/img/unknown-bird.png'}, 'image/png'),
            ('/api/icon-image', {'id': 'eurbla'}, 'image/jpeg'),
        ]:
            with urlopen(self.url + route + '?' + urlencode({**parameters, 'token': self.token})) as response:
                self.assertEqual(response.headers.get_content_type(), mime)
                self.assertTrue(response.read())
        for parameters in [{'path': '../config/config.yaml', 'token': self.token}, {'path': 'assets/img/unknown-bird.png'}]:
            with self.assertRaises(HTTPError):
                urlopen(self.url + '/api/background-image?' + urlencode(parameters))


if __name__ == '__main__':
    unittest.main()
