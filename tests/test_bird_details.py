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
        for scientific_name in ('', 'Pica serica'):
            with self.subTest(scientific_name=scientific_name), tempfile.TemporaryDirectory() as directory:
                entry = {'title': 'Orientelster', 'scientific_name': scientific_name, 'english_name': 'Oriental Magpie'}
                page_id = create_bird_details(directory, entry, Image.new('RGB', (288, 288)), 72, 'Lightroom.exe', 5)
                page = Path(directory) / profile_folder_id(page_id)
                actions = json.loads((page / 'manifest.json').read_text())['Controllers'][0]['Actions']
                names = [actions[f'{i},0'] for i in range(1,4)]
                self.assertEqual([key['Settings']['segment'] for key in names], [0,1,2])
                self.assertEqual(len({key['Settings']['pair'] for key in names}), 1)
                for key in names:
                    self.assertEqual(key['UUID'], 'de.birdtagging.names.scroll')
                    self.assertEqual(key['Settings']['cells'], 3)
                    self.assertEqual(key['Settings']['englishName'], 'Oriental Magpie')
                    self.assertEqual(key['Settings']['scientificName'], scientific_name)
                    self.assertNotIn('Image', key['States'][0])
                self.assertEqual(actions['4,0']['Name'], 'Bird image')
                self.assertEqual(actions['4,0']['Actions'], [])
                self.assertFalse(actions['4,0']['States'][0]['ShowTitle'])

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
                nabu = actions['2,1' if code else '1,1']
                self.assertEqual(nabu['UUID'], 'com.elgato.streamdeck.system.website')
                self.assertEqual(nabu['Settings']['path'], url)
                self.assertEqual(nabu['States'][0]['Title'], 'NABU')
                with Image.open(page / nabu['States'][0]['Image']) as logo:
                    self.assertEqual(logo.size, (72, 72))
                    self.assertIsNotNone(logo.getbbox())
                copy = actions['4,1']
                self.assertEqual(copy['States'][0]['Title'], 'Paste')
                if code:
                    self.assertEqual(actions['1,1']['States'][0]['Title'], 'eBird')
                    self.assertNotEqual(actions['1,1']['States'][0]['Image'], nabu['States'][0]['Image'])

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
                self.assertEqual(actions['0,1']['UUID'], 'com.elgato.streamdeck.multiactions.routine')
                self.assertEqual(actions['0,1']['States'][0]['Title'], 'Tag')
                copy = actions['4,1']
                self.assertEqual(copy['UUID'], 'com.elgato.streamdeck.system.text')
                self.assertEqual(copy['Settings']['pastedText'], 'Bird')
                self.assertFalse(copy['Settings']['isSendingEnter'])
                self.assertFalse(copy['Settings']['isTypingMode'])
                self.assertEqual(copy['States'][0]['Title'], 'Paste')
                if code:
                    self.assertNotEqual(actions['4,0']['States'][0]['Image'], actions['1,1']['States'][0]['Image'])
                    self.assertEqual(actions['1,1']['Settings']['path'], 'https://ebird.org/species/rebfly')
