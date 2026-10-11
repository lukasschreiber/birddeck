import copy
import json
from pathlib import Path
import sys
import tempfile
from threading import Thread
import time
import unittest
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from lightroom_hierarchy import attach_bindings, bind_entries, entries, exchange, load_state, make_plan, save_state, snapshot, sync
from entry_identity import ensure_uuids


def config():
    return {'profile': {'items': [{'type': 'group', 'title': 'Star', 'tag': 'Star (Gruppe)',
        'items': [{'type': 'bird', 'title': 'Star', 'scientific_name': 'Sturnus vulgaris', 'icon': 'eursta'}]}]}}


class HierarchyTests(unittest.TestCase):
    def test_stale_lightroom_updater_is_rejected_before_applying_changes(self):
        with patch('lightroom_hierarchy.exchange', return_value='OK\tSNAPSHOT\ncatalog\n'):
            with self.assertRaisesRegex(ValueError, 'older hierarchy updater'): snapshot()

    def setUp(self):
        self.queue = tempfile.TemporaryDirectory()
        self.queue_patch = patch('lightroom_hierarchy.QUEUE', Path(self.queue.name))
        self.queue_patch.start()
        self.addCleanup(self.queue.cleanup)
        self.addCleanup(self.queue_patch.stop)

    def test_queue_uses_lf_and_empty_catalog_has_empty_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = Path(directory)
            captured = []
            def respond():
                deadline = time.monotonic() + 3
                while time.monotonic() < deadline:
                    requests = list(queue.glob('*.request'))
                    if requests:
                        captured.append(requests[0].read_bytes())
                        requests[0].with_suffix('.response').write_bytes(b'OK\tSNAPSHOT\tINCREMENTAL-2\ncatalog\n')
                        return
                    time.sleep(.01)
            worker = Thread(target=respond)
            worker.start()
            with patch('lightroom_hierarchy.QUEUE', queue):
                self.assertEqual(snapshot(), ('catalog', [], ''))
            worker.join()
            self.assertTrue(captured[0].startswith(b'HIERARCHY\n'))
            self.assertNotIn(b'\r', captured[0])
            self.assertFalse(list(queue.iterdir()))

    def test_moved_renamed_species_retains_id_and_buttons_use_sidecar(self):
        original = config()
        ensure_uuids(original)
        saved = entries(original)
        for i, node in enumerate(saved):
            node['id'] = str(i + 1)
        changed = copy.deepcopy(original)
        bird = changed['profile']['items'][0]['items'].pop()
        bird['title'] = 'Renamed Star'
        changed['profile']['items'].append(bird)
        bound = bind_entries(changed, {'entries': saved})
        self.assertEqual(bound[-1]['id'], '3')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.yaml'
            save_state(path, 'catalog.lrcat', saved)
            attach_bindings(changed, path)
            self.assertEqual(bird['_keyword_uuid'], bird['uuid'])

    def test_species_identity_wins_over_reused_path(self):
        old = {'profile': {'items': [{'type': 'bird', 'title': 'A', 'icon': 'a'},
                                      {'type': 'bird', 'title': 'B', 'icon': 'b'}]}}
        saved = entries(old)
        for i, node in enumerate(saved): node['id'] = str(i + 1)
        old['profile']['items'][0]['title'] = 'B'
        old['profile']['items'][1]['title'] = 'A'
        self.assertEqual([n['id'] for n in bind_entries(old, {'entries': saved})], ['1', '2', '3'])

    def test_uuid_survives_every_identity_attribute_change(self):
        original = config()
        ensure_uuids(original)
        saved = entries(original)
        for i, node in enumerate(saved): node['id'] = str(i + 1)
        group = original['profile']['items'][0]
        group.update(title='New group', tag='New tag')
        bird = group['items'].pop()
        bird.update(title='New bird', scientific_name='New scientific name', icon='new-icon')
        original['profile']['items'].append(bird)
        self.assertEqual([n['id'] for n in bind_entries(original, {'entries': saved})], ['1','2','3'])
        # A new UUID must never steal a saved binding via a reused name/path.
        import uuid
        bird['uuid'] = str(uuid.uuid4())
        self.assertEqual(bind_entries(original, {'entries': saved})[-1]['id'], '')

    def test_fresh_catalog_has_separate_ids_and_duplicate_uuid_is_rejected(self):
        original = config()
        ensure_uuids(original)
        saved = entries(original)
        for i, node in enumerate(saved): node['id'] = str(i+1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.yaml'
            save_state(path, 'E:\\Old.lrcat', saved)
            self.assertEqual(load_state(path, 'F:\\Fresh.lrcat'), {})
            desired, changes = make_plan(original, load_state(path, 'F:\\Fresh.lrcat'), 'F:\\Fresh.lrcat', [])
            self.assertEqual(len(changes), 3)
            self.assertTrue(all(not n['id'] for n in desired))
            for i, node in enumerate(desired): node['id'] = str(i+101)
            save_state(path, 'F:\\Fresh.lrcat', desired)
            self.assertEqual(load_state(path, 'E:\\Old.lrcat')['entries'][-1]['id'], '3')
            self.assertEqual(load_state(path, 'F:\\Fresh.lrcat')['entries'][-1]['id'], '103')
        original['profile']['items'].append(copy.deepcopy(original['profile']['items'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate entry UUID'): ensure_uuids(original)

    def test_saved_uuid_ids_recover_flattened_keywords_without_name_matching_outside_vogel(self):
        data = config()
        ensure_uuids(data)
        saved = entries(data)
        for i, node in enumerate(saved): node['id'] = str(i+1)
        live = [{'id': n['id'], 'name': n['name'], 'path': [n['name']], 'photos': 7} for n in saved]
        desired, changes = make_plan(data, {'catalog': 'catalog', 'entries': saved}, 'catalog', live)
        self.assertEqual([n['id'] for n in desired], ['1','2','3'])
        self.assertEqual(len(changes), 2)
        unbound, _ = make_plan(data, {}, 'catalog', live)
        self.assertFalse(unbound[1]['id'])
        self.assertFalse(unbound[2]['id'])

    def test_populated_old_keyword_wins_and_obsolete_is_archived(self):
        live = [{'id': '1', 'path': ['Vogel'], 'name': 'Vogel', 'photos': 0},
                {'id': '2', 'path': ['Vogel', 'Star (Gruppe)'], 'name': 'Star (Gruppe)', 'photos': 0},
                {'id': '3', 'path': ['Vogel', 'Star (Gruppe)', 'Star'], 'name': 'Star', 'photos': 0},
                {'id': '4', 'path': ['Vogel', 'Star'], 'name': 'Star', 'photos': 17},
                {'id': '5', 'path': ['People'], 'name': 'People', 'photos': 9}]
        desired, changes = make_plan(config(), {}, 'catalog', live)
        self.assertEqual(desired[-1]['id'], '4')
        self.assertTrue(any(c.startswith('Archive:') for c in changes))
        self.assertFalse(any('People' in c for c in changes))

    def test_invalid_ancestor_and_duplicate_siblings_rejected(self):
        data = config()
        del data['profile']['items'][0]['tag']
        with self.assertRaisesRegex(ValueError, 'Ancestor'): entries(data)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            entries({'profile': {'items': [{'type': 'bird', 'title': 'Star'}] * 2}})

    def test_missing_id_wrong_catalog_and_ambiguity_fail(self):
        data = config()
        saved = entries(data)
        saved[0]['id'] = '123'
        with self.assertRaisesRegex(ValueError, 'missing'): make_plan(data, {'entries': saved}, 'catalog', [])
        with self.assertRaisesRegex(ValueError, 'differs'): make_plan(config(), {'catalog': 'other'}, 'catalog', [])
        live = [{'id': str(i), 'path': ['Vogel', str(i), 'Star'], 'name': 'Star', 'photos': 7} for i in range(2)]
        with self.assertRaisesRegex(ValueError, 'Ambiguous'): make_plan(config(), {}, 'catalog', live)

    def test_preview_never_applies_and_verified_apply_saves_new_ids(self):
        data = {'profile': {'items': [{'type': 'bird', 'title': 'Star', 'icon': 'eursta'}]}}
        live = [{'id': '1', 'path': ['Vogel'], 'name': 'Vogel', 'photos': 0}]
        actual = live + [{'id': '2', 'path': ['Vogel', 'Star'], 'name': 'Star', 'photos': 0}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.yaml'
            path.write_text(yaml.safe_dump(data), encoding='utf-8')
            with patch('lightroom_hierarchy.snapshot', return_value=('catalog', live, 'fingerprint\n')), patch('lightroom_hierarchy.exchange') as request:
                sync(path)
                request.assert_not_called()
                self.assertFalse(path.with_suffix('.lightroom.json').exists())
            with patch('lightroom_hierarchy.snapshot', side_effect=[('catalog', live, 'fingerprint\n'), ('catalog', actual, '')]), patch('lightroom_hierarchy.exchange', return_value='OK\tAPPLIED\n1\t1\n2\t2\n'):
                sync(path, True)
                saved = load_state(path, 'catalog')
                self.assertEqual(saved['entries'][-1]['id'], '2')

    def test_changed_photo_count_fails_verification_but_keeps_assigned_ids(self):
        data = {'profile': {'items': [{'type': 'bird', 'title': 'Star'}]}}
        live = [{'id': '1', 'path': ['Vogel'], 'name': 'Vogel', 'photos': 3}]
        actual = [dict(live[0], photos=0), {'id': '2', 'path': ['Vogel', 'Star'], 'name': 'Star', 'photos': 0}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.yaml'
            path.write_text(yaml.safe_dump(data))
            with patch('lightroom_hierarchy.snapshot', side_effect=[('catalog', live, ''), ('catalog', actual, '')]), patch('lightroom_hierarchy.exchange', return_value='OK\tAPPLIED\n1\t1\n2\t2\n'):
                with self.assertRaisesRegex(ValueError, 'photo-assignment'): sync(path, True)
            self.assertTrue(path.with_suffix('.lightroom.json').exists())


if __name__ == '__main__': unittest.main()
