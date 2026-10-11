import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from deduplicate_images import deduplicate_images


class DeduplicationTests(unittest.TestCase):
    def test_images_remain_local_to_each_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('a', 'b'):
                page = root / 'Profiles' / name
                (page / 'Images').mkdir(parents=True)
                for filename in ('one.png', 'two.png'):
                    (page / 'Images' / filename).write_bytes(b'identical image')
                (page / 'manifest.json').write_text(json.dumps({'States': [{'Image': 'Images/one.png'}, {'Image': 'Images/two.png'}]}))
            deduplicate_images(root)
            deduplicate_images(root)
            for page in (root / 'Profiles').iterdir():
                self.assertEqual(len(list((page / 'Images').iterdir())), 1)
                data = json.loads((page / 'manifest.json').read_text())
                for state in data['States']:
                    self.assertTrue(state['Image'].startswith('Images/'))
                    self.assertTrue((page / state['Image']).is_file())
