from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from pagination import sort_elements


class SortingTests(unittest.TestCase):
    def test_uncertain_follows_even_exotic_entries_and_favorites(self):
        entries = [
            {'type': 'uncertain', 'favorite': True},
            {'type': 'bird', 'title': 'Exotic', 'exotic': True},
            {'type': 'uncertain'},
            {'type': 'bird', 'title': 'Regular'},
            {'type': 'bird', 'title': 'Favorite', 'favorite': True},
            {'type': 'group', 'title': 'Exotic group', 'exotic': True},
        ]
        self.assertEqual(sort_elements(entries), [entries[i] for i in (4, 3, 1, 5, 0, 2)])


if __name__ == '__main__':
    unittest.main()
