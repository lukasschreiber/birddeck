from pathlib import Path
import sys
import unittest

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gen_image import remove_largest_white_background


class BackgroundRemovalTests(unittest.TestCase):
    def test_removes_both_sides_of_subject_and_preserves_white_plumage(self):
        image = Image.new('RGB', (80, 80), 'white')
        draw = ImageDraw.Draw(image)
        # Like the Orientelster beak, this subject separates background regions.
        draw.rectangle((10, 0, 40, 79), fill='black')
        draw.rectangle((20, 20, 30, 50), fill='white')
        result = remove_largest_white_background(image)
        self.assertEqual(result.getpixel((3, 40))[3], 0)
        self.assertEqual(result.getpixel((60, 40))[3], 0)
        self.assertEqual(result.getpixel((25, 35)), (255, 255, 255, 255))
        self.assertEqual(result.getpixel((15, 40)), (0, 0, 0, 255))

    def test_enclosed_white_region_is_not_removed_without_border_background(self):
        image = Image.new('RGBA', (40, 40), 'black')
        ImageDraw.Draw(image).rectangle((5, 5, 34, 34), fill='white')
        self.assertEqual(remove_largest_white_background(image).tobytes(), image.tobytes())

    def test_existing_transparency_is_preserved(self):
        image = Image.new('RGBA', (40, 40), (20, 40, 60, 100))
        ImageDraw.Draw(image).rectangle((0, 0, 10, 39), fill='white')
        result = remove_largest_white_background(image)
        self.assertEqual(result.getpixel((5, 20))[3], 0)
        self.assertEqual(result.getpixel((30, 20)), (20, 40, 60, 100))
