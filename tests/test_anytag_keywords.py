import csv
from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from anytag_keywords import HEADER, generate_anytag, read_catalog


class AnyTagTests(unittest.TestCase):
    def setup_files(self, directory):
        root = Path(directory)
        config, source, output = root / 'config.yaml', root / 'catalog.csv', root / 'update.csv'
        config.write_text(yaml.safe_dump({'profile': {'items': [
            {'type': 'group', 'title': 'Lauf-vögel', 'tag': 'Laufvögel', 'items': [
                {'type': 'bird', 'title': 'Nandu'}]}]}}, allow_unicode=True), encoding='utf-8')
        rows = [HEADER, ['C:\\Photos\\catalog.lrcat'],
                ['1', '0', 'N', 'Y', 'N', 'N', 'N', '1', 'Vogel'],
                ['2', '0', 'Y', 'Y', 'Y', 'N', 'N', '2', '', 'Lauf-vögel', 'Vogel'],
                ['3', '4', 'N', 'Y', 'N', 'N', 'N', '3', '', '', 'Nandu', 'Lauf-vögel < Vogel'],
                ['', '', '', '', '', '', 'Y', '4', '', '', '', 'Rhea', 'Nandu < Lauf-vögel < Vogel'],
                ['5', '2', 'Y', 'Y', 'Y', 'N', 'N', '2', '', 'Unmanaged', 'Vogel'],
                ['4', '7', 'Y', 'Y', 'Y', 'Y', 'N', '1', 'Menschen']]
        with source.open('w', encoding='utf-8-sig', newline='') as handle:
            csv.writer(handle).writerows(rows)
        return config, source, output

    def test_binding_preserves_assignments_attributes_synonyms_and_unmanaged(self):
        with tempfile.TemporaryDirectory() as directory:
            config, source, output = self.setup_files(directory)
            generate_anytag(config, source, output, bind=True)
            data = yaml.safe_load(config.read_text(encoding='utf-8'))
            self.assertEqual(data['profile']['items'][0]['anytag_id'], '2')
            bird = data['profile']['items'][0]['items'].pop()
            bird['title'] = 'Renamed Nandu'
            data['profile']['items'].append(bird)
            config.write_text(yaml.safe_dump(data, allow_unicode=True), encoding='utf-8')
            generate_anytag(config, source, output)
            preamble, nodes = read_catalog(output)
            by_id = {n['attrs'][0]: n for n in nodes if n['attrs'][0]}
            self.assertEqual(preamble[1], ['C:\\Photos\\catalog.lrcat'])
            self.assertEqual(by_id['3']['path'], ('Vogel', 'Renamed Nandu'))
            self.assertEqual(by_id['3']['attrs'][1:7], ['4', 'N', 'Y', 'N', 'N', 'N'])
            self.assertEqual(by_id['3']['children'][0]['name'], 'Rhea')
            self.assertEqual(by_id['2']['name'], 'Laufvögel')
            self.assertEqual(by_id['4']['name'], 'Menschen')
            self.assertNotIn('5', by_id)

    def test_wrong_catalog_and_missing_ids_fail_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            config, source, output = self.setup_files(directory)
            data = yaml.safe_load(config.read_text(encoding='utf-8'))
            data['profile']['anytag_catalog'] = 'different.lrcat'
            config.write_text(yaml.safe_dump(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'different Lightroom catalog'):
                generate_anytag(config, source, output)
            self.assertFalse(output.exists())
            data['profile'].pop('anytag_catalog')
            data['profile']['anytag_id'] = '999'
            config.write_text(yaml.safe_dump(data), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'missing from export'):
                generate_anytag(config, source, output)

    def test_ambiguous_name_requires_explicit_id(self):
        with tempfile.TemporaryDirectory() as directory:
            config, source, output = self.setup_files(directory)
            data = yaml.safe_load(config.read_text(encoding='utf-8'))
            data['profile']['items'] = [{'type': 'bird', 'title': 'Nandu'}]
            config.write_text(yaml.safe_dump(data), encoding='utf-8')
            with source.open('a', encoding='utf-8', newline='') as handle:
                csv.writer(handle).writerows([
                    ['6', '0', 'Y', 'Y', 'Y', 'N', 'N', '1', 'Vogel'],
                    ['7', '2', 'Y', 'Y', 'Y', 'N', 'N', '2', '', 'Nandu', 'Vogel']])
            with self.assertRaisesRegex(ValueError, 'Ambiguous keyword|Multiple populated'):
                generate_anytag(config, source, output)
            self.assertFalse(output.exists())

    def test_populated_old_keyword_replaces_empty_bound_keyword(self):
        with tempfile.TemporaryDirectory() as directory:
            config, source, output = self.setup_files(directory)
            data = yaml.safe_load(config.read_text(encoding='utf-8'))
            data['profile']['items'][0]['items'][0]['anytag_id'] = '3'
            config.write_text(yaml.safe_dump(data, allow_unicode=True), encoding='utf-8')
            with source.open(encoding='utf-8-sig', newline='') as handle:
                rows = list(csv.reader(handle))
            next(r for r in rows if r[0] == '3')[1] = '0'
            rows.insert(-1, ['7', '12', 'Y', 'Y', 'Y', 'N', 'N', '2', '', 'Nandu', 'Vogel'])
            with source.open('w', encoding='utf-8-sig', newline='') as handle:
                csv.writer(handle).writerows(rows)
            generate_anytag(config, source, output, bind=True)
            _, nodes = read_catalog(output)
            by_id = {n['attrs'][0]: n for n in nodes}
            self.assertNotIn('3', by_id)
            self.assertEqual(by_id['7']['path'], ('Vogel', 'Laufvögel', 'Nandu'))
            self.assertEqual(by_id['7']['attrs'][1], '12')
            updated = yaml.safe_load(config.read_text(encoding='utf-8'))
            self.assertEqual(updated['profile']['items'][0]['items'][0]['anytag_id'], '7')

    def test_former_flat_bird_identity_goes_to_child_not_new_group(self):
        with tempfile.TemporaryDirectory() as directory:
            config, source, output = self.setup_files(directory)
            data = {'profile': {'items': [{'type': 'group', 'title': 'Nandu', 'anytag_id': '3',
                                         'items': [{'type': 'bird', 'title': 'Nandu'}]}]}}
            config.write_text(yaml.safe_dump(data), encoding='utf-8')
            generate_anytag(config, source, output, bind=True)
            _, nodes = read_catalog(output)
            bird = next(n for n in nodes if n['attrs'][0] == '3')
            self.assertEqual(bird['path'], ('Vogel', 'Nandu', 'Nandu'))
            self.assertEqual(bird['parent']['attrs'][0], '')
