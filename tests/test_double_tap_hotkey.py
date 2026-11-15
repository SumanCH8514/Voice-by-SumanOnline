from __future__ import annotations

import time
import unittest

from voice_by_sumanonline.hotkey import PushToTalk

class TestPushToTalkDoubleTap(unittest.TestCase):
    def test_hold_to_talk(self):
        press_count = 0
        release_count = 0

        def on_press():
            nonlocal press_count
            press_count += 1

        def on_release():
            nonlocal release_count
            release_count += 1

        ptt = PushToTalk(
            on_press=on_press,
            on_release=on_release,
            double_tap_interval=0.20,
        )

        ptt._handle_press()
        self.assertEqual(press_count, 1)
        self.assertEqual(release_count, 0)

        time.sleep(0.25)
        ptt._handle_release()
        self.assertEqual(release_count, 1)
        self.assertFalse(ptt.is_latched)

    def test_double_tap_hands_free_and_stop(self):
        press_count = 0
        release_count = 0

        def on_press():
            nonlocal press_count
            press_count += 1

        def on_release():
            nonlocal release_count
            release_count += 1

        ptt = PushToTalk(
            on_press=on_press,
            on_release=on_release,
            double_tap_interval=0.25,
        )

        ptt._handle_press()
        self.assertEqual(press_count, 1)
        self.assertEqual(release_count, 0)

        time.sleep(0.05)
        ptt._handle_release()
        self.assertEqual(release_count, 0)
        self.assertFalse(ptt.is_latched)

        time.sleep(0.08)
        ptt._handle_press()
        self.assertEqual(press_count, 1)
        self.assertEqual(release_count, 0)
        self.assertTrue(ptt.is_latched)

        time.sleep(0.05)
        ptt._handle_release()
        self.assertEqual(release_count, 0)
        self.assertTrue(ptt.is_latched)

        time.sleep(0.10)
        ptt._handle_press()
        self.assertEqual(release_count, 1)
        self.assertFalse(ptt.is_latched)

        ptt._handle_release()
        self.assertEqual(release_count, 1)

    def test_single_tap_timeout(self):
        press_count = 0
        release_count = 0

        def on_press():
            nonlocal press_count
            press_count += 1

        def on_release():
            nonlocal release_count
            release_count += 1

        ptt = PushToTalk(
            on_press=on_press,
            on_release=on_release,
            double_tap_interval=0.15,
        )

        ptt._handle_press()
        self.assertEqual(press_count, 1)
        self.assertEqual(release_count, 0)

        time.sleep(0.03)
        ptt._handle_release()
        self.assertEqual(release_count, 0)

        time.sleep(0.25)
        self.assertEqual(release_count, 1)
        self.assertFalse(ptt.is_latched)

if __name__ == "__main__":
    unittest.main()
