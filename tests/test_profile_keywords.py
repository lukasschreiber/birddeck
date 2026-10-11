from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from generate_bird_profile import create_profile


class ProfileKeywordTests(unittest.TestCase):
    def test_profile_creation_refreshes_keywords_from_custom_config(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / 'custom.yaml'
            output = root / 'export'
            output.mkdir()
            keywords = output / 'LightroomKeywords.txt'
            keywords.write_text('stale')
            config.write_text(yaml.safe_dump({'profile': {
                'name': 'Test', 'lightroom': '', 'model': '20GBA9901',
                'size': {'columns': 5, 'rows': 3},
                'items': [{'type': 'group', 'title': 'Gruppe', 'tag': 'Vögel',
                           'items': [{'type': 'bird', 'title': 'Grünfink'}]}]
            }}, allow_unicode=True), encoding='utf-8')
            with patch('generate_bird_profile.generate_image') as render:
                from PIL import Image
                render.return_value = Image.new('RGB', (288, 288))
                profile = create_profile(config, output)
            self.assertTrue(profile.is_file())
            self.assertEqual(keywords.read_text(encoding='utf-8'), 'Vogel\n\tVögel\n\t\tGrünfink')
