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
    def test_name_key_is_display_only_and_scientific_name_is_optional(self):
        from name_key import render_name_key
        from profile_images import save_key_image
        from io import BytesIO
        for scientific_name in ('', 'Pica serica'):
            with self.subTest(scientific_name=scientific_name), tempfile.TemporaryDirectory() as directory:
                entry = {'title': 'Orientelster', 'scientific_name': scientific_name}
                page_id = create_bird_details(directory, entry, Image.new('RGB', (288, 288)), 72, 'Lightroom.exe', 5)
                page = Path(directory) / profile_folder_id(page_id)
                actions = json.loads((page / 'manifest.json').read_text())['Controllers'][0]['Actions']
                name_key = actions['3,0']
                self.assertEqual(name_key['Name'], 'Bird name')
                self.assertEqual(name_key['Actions'], [])
                self.assertFalse(name_key['States'][0]['ShowTitle'])
                expected = BytesIO()
                save_key_image(render_name_key(entry['title'], scientific_name), expected, 72)
                self.assertEqual((page / name_key['States'][0]['Image']).read_bytes(), expected.getvalue())

    def test_nabu_action_with_and_without_ebird(self):
        url = 'https://www.nabu.de/tiere-und-pflanzen/voegel/portraets/amsel/'
        for code in ('eurbla', None):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                entry = {'title': 'Amsel', 'nabu': url}
                if code:
                    entry['icon'] = code
                page_id = create_bird_details(directory, entry, Image.new('RGB', (288, 288)), 72, 'Lightroom.exe', 5)
                page = Path(directory) / profile_folder_id(page_id)
                actions = json.loads((page / 'manifest.json').read_text())['Controllers'][0]['Actions']
                nabu = actions['3,0' if code else '2,0']
                self.assertEqual(nabu['UUID'], 'com.elgato.streamdeck.system.website')
                self.assertEqual(nabu['Settings']['path'], url)
                self.assertEqual(nabu['States'][0]['Title'], 'NABU')
                with Image.open(page / nabu['States'][0]['Image']) as logo:
                    self.assertEqual(logo.size, (72, 72))
                    self.assertIsNotNone(logo.getbbox())
                copy = actions['4,0' if code else '3,0']
                self.assertEqual(copy['States'][0]['Title'], 'Paste')
                if code:
                    self.assertEqual(actions['2,0']['States'][0]['Title'], 'eBird')
                    self.assertNotEqual(actions['2,0']['States'][0]['Image'], nabu['States'][0]['Image'])

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
                self.assertEqual(copy['UUID'], 'com.elgato.streamdeck.system.text')
                self.assertEqual(copy['Settings']['pastedText'], 'Bird')
                self.assertFalse(copy['Settings']['isSendingEnter'])
                self.assertFalse(copy['Settings']['isTypingMode'])
                self.assertEqual(copy['States'][0]['Title'], 'Paste')
                if code:
                    self.assertNotEqual(actions['1,0']['States'][0]['Image'], actions['2,0']['States'][0]['Image'])
                    self.assertEqual(actions['2,0']['Settings']['path'], 'https://ebird.org/species/rebfly')
