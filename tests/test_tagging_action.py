import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gen_action import generate_bird_action


class TaggingActionTests(unittest.TestCase):
    def test_waits_for_focus_and_paste_before_committing(self):
        steps = generate_bird_action('Star', 'image', '')['Actions'][0]['Actions']
        self.assertEqual(steps[0]['Settings']['Hotkeys'][0]['VKeyCode'], 75)
        self.assertEqual(steps[1]['UUID'], 'com.elgato.streamdeck.multiactions.delay')
        self.assertGreaterEqual(steps[1]['Settings']['delay'], 500)
        self.assertEqual(steps[2]['Settings']['pastedText'], 'Star')
        self.assertFalse(steps[2]['Settings']['isSendingEnter'])
        self.assertEqual(steps[3]['UUID'], 'com.elgato.streamdeck.multiactions.delay')
        self.assertEqual(steps[4]['Settings']['Hotkeys'][0]['VKeyCode'], 9)
        self.assertEqual(steps[5]['UUID'], 'com.elgato.streamdeck.multiactions.delay')
        self.assertEqual(steps[6]['Settings']['Hotkeys'][0]['VKeyCode'], 13)
        self.assertEqual(steps[7]['UUID'], 'com.elgato.streamdeck.multiactions.delay')
        self.assertEqual(steps[8]['Settings']['Hotkeys'][0]['VKeyCode'], 27)
