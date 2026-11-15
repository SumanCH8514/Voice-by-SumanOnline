from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from voice_by_sumanonline.audio import Recorder, SILENCE_PEAK_THRESHOLD
from voice_by_sumanonline.config import default_config, get_dictionary, load_config, save_config
from voice_by_sumanonline.dictionary import apply_dictionary, compile_dictionary
from voice_by_sumanonline.format import clean_transcript
from voice_by_sumanonline.hotkey import PushToTalk
from voice_by_sumanonline.keychain import SERVICE_NAME, KEY_NAME, get_api_key, set_api_key
from voice_by_sumanonline.preview import is_model_cached
from voice_by_sumanonline import startup

class TestPhase5AudioResilience(unittest.TestCase):
    def test_recorder_instantiation(self):
        rec = Recorder()
        self.assertIsNotNone(rec)

    def test_digital_silence_detection(self):
        silence_triggered = []
        def on_silence():
            silence_triggered.append(True)

        rec = Recorder(on_silence_fallback=on_silence)
        rec._stream = MagicMock()
        rec._audio_callback(
            np.zeros((1600, 1), dtype=np.float32),
            1600,
            {},
            0,
        )
        self.assertIsNotNone(rec._silence_started_at)

class TestPersonalDictionary(unittest.TestCase):
    def test_case_insensitive_word_boundary_replacement(self):
        pairs = [
            ("pie torch", "PyTorch"),
            ("kubernetes", "K8s"),
            ("next js", "Next.js"),
            ("grpc", "gRPC"),
        ]
        compiled = compile_dictionary(pairs)
        raw = "I am deploying a pie torch model to kubernetes using next js and grpc."
        out = apply_dictionary(raw, compiled)
        self.assertEqual(
            out,
            "I am deploying a PyTorch model to K8s using Next.js and gRPC.",
        )

    def test_word_boundary_prevents_partial_replacement(self):
        pairs = [("k8s", "Kubernetes")]
        compiled = compile_dictionary(pairs)
        raw = "The k8s cluster is healthy, but k8ssandra is still pending."
        out = apply_dictionary(raw, compiled)
        self.assertEqual(
            out,
            "The Kubernetes cluster is healthy, but k8ssandra is still pending.",
        )

class TestConfigAndKeychain(unittest.TestCase):
    def test_api_key_not_written_to_config(self):
        with tempfile.TemporaryDirectory() as td:
            cfg_path = Path(td) / "config.json"
            cfg = default_config()
            cfg["api_key"] = "secret_groq_key_123"
            save_config(cfg, cfg_path)
            with open(cfg_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertNotIn("api_key", saved)
            self.assertNotIn("groq_api_key", saved)

    def test_keychain_service_name(self):
        self.assertEqual(SERVICE_NAME, "Voice by SumanOnline")
        self.assertEqual(KEY_NAME, "groq_api_key")

if __name__ == "__main__":
    unittest.main()
