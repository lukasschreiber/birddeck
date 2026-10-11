from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gen_image import generate_image
from web_editor import render_preview


class ImageRotationTests(unittest.TestCase):
    def test_clockwise_rotation_and_preview_match(self):
        # An asymmetric subject makes the rotation direction observable.
        bird = Image.new('RGBA', (40, 20), 'red')
        for x in range(20, 40):
            for y in range(20):
                bird.putpixel((x, y), (0, 0, 255, 255))
        with tempfile.TemporaryDirectory() as directory, \
                patch('gen_image.PROJECT_CACHE_DIR', Path(directory)), \
                patch('gen_image.fetch_image', side_effect=lambda _: bird.copy()):
            original = generate_image('eurgre1', '#00ff00', (288, 288))
            rotated = generate_image('eurgre1', '#00ff00', (288, 288), rotation=90)
            self.assertEqual(original.getpixel((130, 144)), (255, 0, 0))
            self.assertEqual(rotated.getpixel((144, 130)), (255, 0, 0))
            self.assertEqual(rotated.getpixel((144, 158)), (0, 0, 255))
            self.assertEqual(rotated.getpixel((50, 50)), (0, 255, 0))
            preview = render_preview({'type': 'bird', 'icon': 'eurgre1',
                                      'color': '#00ff00', 'rotation': 90}, {'eurgre1': 1})
            self.assertEqual(Image.open(BytesIO(preview)).tobytes(), rotated.tobytes())


if __name__ == '__main__':
    unittest.main()
