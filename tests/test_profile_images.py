from io import BytesIO
from pathlib import Path
import sys
import unittest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from profile_images import image_size, save_key_image


class ProfileImageTests(unittest.TestCase):
    def test_default_and_configured_sizes(self):
        self.assertEqual(image_size({}), 72)
        for pixels in (72, 144, 288):
            output = BytesIO()
            save_key_image(Image.new('RGB', (288, 288), 'red'), output, image_size({'image_size': pixels}))
            self.assertEqual(Image.open(output).size, (pixels, pixels))

    def test_invalid_sizes(self):
        for value in (True, 0, 1025, '72', 72.5):
            with self.assertRaises(ValueError):
                image_size({'image_size': value})
