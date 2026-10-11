from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from pagination import paginate_elements, sort_elements


class SortingTests(unittest.TestCase):
    def test_exotic_entries_sort_by_country_then_name_across_pages(self):
        entries = [
            {'type': 'bird', 'title': 'Alpha', 'exotic': True, 'country': 'TZ'},
            {'type': 'bird', 'title': 'Zebra', 'exotic': True, 'country': 'KR'},
            {'type': 'group', 'title': 'a-lpha', 'exotic': True, 'country': ' kr '},
            {'type': 'bird', 'title': 'Unknown', 'exotic': True},
            {'type': 'bird', 'title': 'Zulu', 'country': 'DE'},
            {'type': 'bird', 'title': 'Beta', 'country': 'TZ'},
            {'type': 'bird', 'title': 'Favorite', 'favorite': True,
             'exotic': True, 'country': 'TZ'},
        ]
        expected = [entries[i] for i in (6, 5, 4, 3, 2, 1, 0)]
        self.assertEqual(sort_elements(entries), expected)
        pages = paginate_elements(entries, 4)
        self.assertEqual([entry for page in pages for entry in page], expected)

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
