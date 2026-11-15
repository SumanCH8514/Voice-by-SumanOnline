from __future__ import annotations

import unittest
import numpy as np

from voice_by_sumanonline.preview import StreamingPreview, QUEUE_MAXSIZE, RATE_LIMIT_HZ
from voice_by_sumanonline.hud import HUD

class TestPreviewAndHUD(unittest.TestCase):
    def test_queue_maxsize(self):
        p = StreamingPreview(on_partial=lambda t: None)
        self.assertEqual(p._queue.maxsize, 8)

    def test_rate_limiting(self):
        self.assertLessEqual(RATE_LIMIT_HZ, 15)

    def test_two_model_separation(self):
        from voice_by_sumanonline.main import _run_finalize

        injected_texts = []
        def fake_inject(t):
            injected_texts.append(t)
            return True

        class DummyHUD:
            def __init__(self):
                self.preview_text = ""
                self.status_text = ""
            def set_preview_text(self, t):
                self.preview_text = t
            def set_status_text(self, t):
                self.status_text = t
            def hide(self):
                pass

        dummy_hud = DummyHUD()
        dummy_hud.set_preview_text("provisional vosk text")

        audio = np.zeros(16000, dtype=np.float32)
        _run_finalize(audio, dummy_hud, inject_fn=fake_inject)
        self.assertNotIn("provisional vosk text", injected_texts)

if __name__ == "__main__":
    unittest.main()
