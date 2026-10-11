import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bird_details import create_bird_details
from gen_uuid import profile_folder_id


class BirdDetailTests(unittest.TestCase):
    def test_tagging_and_optional_website(self):
        for code in ('rebfly', None):
            with tempfile.TemporaryDirectory() as directory:
                entry = {'title': 'Bird'}
                if code:
                    entry['icon'] = code
                page_id = create_bird_details(directory, entry, Image.new('RGB', (288, 288)), 72, 'Lightroom.exe', 5)
                manifest = Path(directory) / profile_folder_id(page_id) / 'manifest.json'
                actions = json.loads(manifest.read_text())['Controllers'][0]['Actions']
                self.assertEqual(actions['0,0']['UUID'], 'com.elgato.streamdeck.profile.backtoparent')
                self.assertEqual(actions['1,0']['UUID'], 'com.elgato.streamdeck.multiactions.routine')
                self.assertEqual(actions['1,0']['States'][0]['Title'], 'Tag')
                copy = actions['3,0' if code else '2,0']
                self.assertEqual(copy['UUID'], 'com.elgato.streamdeck.system.openapp')
                import base64
                encoded = copy['Settings']['args'].split()[-1]
                self.assertEqual(base64.b64decode(encoded).decode('utf-16-le'), "Set-Clipboard -Value 'Bird'")
                if code:
                    self.assertNotEqual(actions['1,0']['States'][0]['Image'], actions['2,0']['States'][0]['Image'])
                    self.assertEqual(actions['2,0']['Settings']['path'], 'https://ebird.org/species/rebfly')
