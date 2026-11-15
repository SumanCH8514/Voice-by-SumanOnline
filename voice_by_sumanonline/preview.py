from __future__ import annotations

import json
import logging
import queue
import socket
import threading
import time
import urllib.request
import zipfile
from math import gcd
from pathlib import Path
from typing import Callable, Optional

import numpy as np
from scipy import signal

log = logging.getLogger("voice_by_sumanonline.preview")

VOSK_MODEL_NAME = "vosk-model-small-en-us-0.15"
VOSK_MODEL_URL = f"https://alphacephei.com/vosk/models/{VOSK_MODEL_NAME}.zip"
CACHE_DIR = Path.home() / ".cache" / "voice_by_sumanonline" / "models"

QUEUE_MAXSIZE = 8
RATE_LIMIT_HZ = 15
PREVIEW_SR = 16_000
DOWNLOAD_TIMEOUT_S = 120

def get_active_model_dir() -> Path:
    return CACHE_DIR / VOSK_MODEL_NAME

def is_model_cached() -> bool:
    target_dir = get_active_model_dir()
    return target_dir.exists() and any(target_dir.iterdir())

def download_model(progress_cb: Optional[Callable[[int, int], None]] = None) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target_dir = get_active_model_dir()
    if target_dir.exists() and any(target_dir.iterdir()):
        if progress_cb:
            progress_cb(1, 1)
        return target_dir

    zip_path = CACHE_DIR / f"{VOSK_MODEL_NAME}.zip"
    if not zip_path.exists():
        log.info("Downloading Vosk model (~40 MB) to %s ...", zip_path)
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(float(DOWNLOAD_TIMEOUT_S))
        try:
            def reporthook(block_num: int, block_size: int, total_size: int) -> None:
                if progress_cb:
                    downloaded = block_num * block_size
                    if total_size > 0:
                        downloaded = min(downloaded, total_size)
                    progress_cb(downloaded, total_size)

            urllib.request.urlretrieve(VOSK_MODEL_URL, zip_path, reporthook=reporthook)
        finally:
            socket.setdefaulttimeout(old_timeout)
        log.info("Download complete.")

    log.info("Extracting Vosk model...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(CACHE_DIR)
    log.info("Extraction complete.")
    if progress_cb:
        progress_cb(1, 1)
    return CACHE_DIR / VOSK_MODEL_NAME

def _ensure_model() -> Path:
    return download_model()

class StreamingPreview:
    def __init__(self, on_partial: Optional[Callable[[str], None]] = None) -> None:
        self._on_partial = on_partial
        self._queue: queue.Queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
        self._model = None
        self._rec = None
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._resample_up = 1
        self._resample_down = 1
        self._configured_sr = 0
        self._ready = False
        self._last_emit_time = 0.0
        self._emit_interval = 1.0 / RATE_LIMIT_HZ
        self._last_text = ""
        self._lock = threading.Lock()

    def set_on_partial(self, cb: Optional[Callable[[str], None]]) -> None:
        self._on_partial = cb

    def is_ready(self) -> bool:
        return self._ready

    def initialize(self) -> bool:
        with self._lock:
            if self._ready:
                return True
            try:
                from vosk import KaldiRecognizer, Model, SetLogLevel
            except ImportError:
                log.info("Vosk not installed; live streaming preview disabled.")
                return False

            SetLogLevel(-1)
            try:
                model_dir = _ensure_model()
            except Exception as e:
                log.warning("Could not download Vosk model: %s", e)
                return False

            try:
                self._model = Model(str(model_dir))
                self._rec = KaldiRecognizer(self._model, float(PREVIEW_SR))
                self._rec.SetWords(False)
            except Exception as e:
                log.warning("Vosk init failed: %s", e)
                return False

            self._ready = True
            log.info("Vosk streaming preview ready.")
            return True

    def configure_input_rate(self, sample_rate: int) -> None:
        if sample_rate <= 0 or sample_rate == self._configured_sr:
            return
        self._configured_sr = sample_rate
        g = gcd(PREVIEW_SR, sample_rate)
        self._resample_up = PREVIEW_SR // g
        self._resample_down = sample_rate // g

    def start(self) -> None:
        if not self._ready:
            return
        self._stop_event.clear()
        self._drain_queue()
        self._last_text = ""
        self._last_emit_time = 0.0

        if self._rec is not None and self._model is not None:
            from vosk import KaldiRecognizer
            self._rec = KaldiRecognizer(self._model, float(PREVIEW_SR))
            self._rec.SetWords(False)

        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="VoskPreviewWorker",
            daemon=True,
        )
        self._worker_thread.start()

    def stop(self) -> None:
        if not self._ready or self._worker_thread is None:
            return
        self._stop_event.set()
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        self._worker_thread.join(timeout=1.0)
        self._worker_thread = None
        self._drain_queue()

    def feed_audio(self, chunk: np.ndarray) -> None:
        if not self._ready or self._stop_event.is_set():
            return
        try:
            self._queue.put_nowait(chunk)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(chunk)
            except queue.Full:
                pass

    def _drain_queue(self) -> None:
        while True:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if item is None:
                break

            try:
                pcm_bytes = self._prepare_chunk(item)
            except Exception as e:
                log.debug("Chunk preparation failed: %s", e)
                continue

            if not pcm_bytes or self._rec is None:
                continue

            try:
                self._rec.AcceptWaveform(pcm_bytes)
                res = json.loads(self._rec.PartialResult())
                text = (res.get("partial") or "").strip()
            except Exception as e:
                log.debug("Vosk decode failed: %s", e)
                continue

            if not text:
                continue

            now = time.monotonic()
            if text != self._last_text or (now - self._last_emit_time) >= self._emit_interval:
                self._last_text = text
                self._last_emit_time = now
                cb = self._on_partial
                if cb is not None:
                    try:
                        cb(text)
                    except Exception as e:
                        log.debug("Partial callback failed: %s", e)

    def _prepare_chunk(self, chunk: np.ndarray) -> bytes:
        if chunk.ndim == 2:
            if chunk.shape[1] == 1:
                mono = chunk[:, 0]
            else:
                mono = chunk.mean(axis=1)
        else:
            mono = chunk

        if self._configured_sr and self._configured_sr != PREVIEW_SR:
            resampled = signal.resample_poly(
                mono, self._resample_up, self._resample_down
            )
        else:
            resampled = mono

        clipped = np.clip(resampled, -1.0, 1.0)
        int16 = (clipped * 32767.0).astype(np.int16)
        return int16.tobytes()
