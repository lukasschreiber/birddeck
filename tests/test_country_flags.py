from io import BytesIO
from pathlib import Path
import sys
import unittest

from PIL import Image, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from country_flags import COUNTRIES, flag_path
from gen_image import generate_image
from web_editor import render_preview


class CountryFlagTests(unittest.TestCase):
    def test_all_country_assets_are_valid_images(self):
        self.assertEqual(len(COUNTRIES), 249)
        for code in COUNTRIES:
            with Image.open(flag_path(code)) as flag:
                flag.verify()

    def test_flag_is_bottom_left_and_only_shown_for_exotic(self):
        for pixels in (72, 144, 288):
            base = generate_image('', '#00ff00', (pixels, pixels), exotic=True)
            flagged = generate_image('', '#00ff00', (pixels, pixels), exotic=True, country='DE')
            bounds = ImageChops.difference(base, flagged).getbbox()
            self.assertIsNotNone(bounds)
            self.assertGreater(bounds[0], pixels * 0.07)
            self.assertGreater(bounds[1], pixels * 0.70)
            self.assertLess(bounds[2], pixels * 0.35)
            self.assertLess(bounds[3], pixels * 0.93)
            plain = generate_image('', '#00ff00', (pixels, pixels), country='DE')
            self.assertEqual(plain.tobytes(), base.tobytes())
        preview = Image.open(BytesIO(render_preview(
            {'type': 'group', 'exotic': True, 'country': 'DE', 'bg': '#00ff00'}, {})))
        self.assertEqual(preview.tobytes(), flagged.tobytes())


if __name__ == '__main__':
    unittest.main()
