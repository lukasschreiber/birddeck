from pathlib import Path
import sys
import unittest
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from name_key import render_name_key, fit_lines


class NameKeyTests(unittest.TestCase):
    def test_orientelster_uses_readable_font_sizes_and_true_black(self):
        image = render_name_key('Orientelster', 'Pica serica')
        self.assertEqual(image.getpixel((0, 0)), (0, 0, 0))
        self.assertEqual(image.getpixel((144, 10)), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        lines, common_font, _ = fit_lines('Orientelster', draw, 56)
        self.assertEqual(lines, ['Orient', 'elster'])
        self.assertGreaterEqual(common_font.size / 4, 13)
        _, scientific_font, _ = fit_lines('Pica serica', draw, 44, italic=True, max_height=100)
        self.assertGreaterEqual(scientific_font.size / 4, 11)

    def test_long_names_fit_inside_the_key(self):
        for common, scientific in (
            ('China-Fleckschnabelente', 'Anas zonorhyncha'),
            ('Weißflügel-Seeschwalbe', 'Chlidonias leucopterus'),
            ('Halsband-Zwergfalke', 'Microhierax caerulescens'),
            ('Bird ' * 30, 'Species ' * 25),
        ):
            image = render_name_key(common, scientific)
            background = Image.new('RGB', image.size, '#000000')
            x1, y1, x2, y2 = ImageChops.difference(image, background).getbbox()
            self.assertGreater(x1, 15)
            self.assertGreater(y1, 15)
            self.assertLess(x2, 273)
            self.assertLess(y2, 273)

    def test_display_hyphens_and_optional_scientific_name(self):
        self.assertEqual(render_name_key('Sing-vögel').tobytes(), render_name_key('Singvögel').tobytes())
        self.assertNotEqual(render_name_key('Sing-Vögel').tobytes(), render_name_key('SingVögel').tobytes())
        self.assertNotEqual(render_name_key('Orientelster').tobytes(), render_name_key('Orientelster', 'Pica serica').tobytes())
