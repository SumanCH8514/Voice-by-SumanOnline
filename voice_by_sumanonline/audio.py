from __future__ import annotations

import logging
import sys
import threading
import time
from typing import Callable, List, Optional, Tuple

import numpy as np
import sounddevice as sd
from scipy import signal

log = logging.getLogger("voice_by_sumanonline.audio")

TARGET_SR = 16_000
SILENCE_PEAK_THRESHOLD = 1e-6
SILENCE_DURATION_S = 1.5

_PreferredBuiltinNames = (
    "macbook",
    "built-in",
    "built in",
    "internal",
    "system default",
)

class Recorder:
    def __init__(
        self,
        on_silence_fallback: Optional[Callable[[], None]] = None,
        silence_callback: Optional[Callable[[], None]] = None,
        on_rms: Optional[Callable[[float], None]] = None,
    ) -> None:
        self._stream: Optional[sd.InputStream] = None
        self._buffers: List[np.ndarray] = []
        self._lock = threading.Lock()
        self._native_sr: int = TARGET_SR
        self._native_channels: int = 1
        self._device_name: str = ""
        self._device_index: Optional[int] = None
        self._preview_sink: Optional[Callable[[np.ndarray], None]] = None
        self.start_time: Optional[float] = None
        self._silence_started_at: Optional[float] = None
        self._silence_callback: Optional[Callable[[], None]] = (
            on_silence_fallback or silence_callback
        )
        self._on_rms = on_rms
        self._device_lock: Optional[Tuple[Optional[int], Optional[str]]] = None

    @property
    def native_sample_rate(self) -> int:
        return self._native_sr

    @property
    def native_sr(self) -> int:
        return self._native_sr

    @property
    def native_channels(self) -> int:
        return self._native_channels

    @property
    def device_name(self) -> str:
        return self._device_name

    @property
    def device_index(self) -> Optional[int]:
        if self._device_lock is not None and self._device_lock[0] is not None:
            return self._device_lock[0]
        return self._device_index

    def set_on_rms(self, cb: Optional[Callable[[float], None]]) -> None:
        self._on_rms = cb

    def set_preview_sink(self, sink: Optional[Callable[[np.ndarray], None]]) -> None:
        self._preview_sink = sink

    def lock_device(
        self,
        index: Optional[int] = None,
        name_substring: Optional[str] = None,
    ) -> None:
        with self._lock:
            if index is None and (not name_substring):
                self._device_lock = None
            else:
                self._device_lock = (index, name_substring)

    def start(self) -> None:
        with self._lock:
            if self._stream is not None:
                return
            self._buffers.clear()
            self._silence_started_at = None

            device_idx = self._resolve_target_device()
            try:
                self._open_stream(device_idx)
            except Exception as e:
                log.warning(
                    "Failed to open audio device %s: %s; re-init & fallback",
                    device_idx, e,
                )
                self._stream = None
                self._reinit_portaudio()
                fallback_idx = self._find_fallback_device()
                try:
                    self._open_stream(fallback_idx)
                except Exception as e2:
                    log.error("Audio open fallback failed: %s", e2)
                    self._stream = None
                    raise

            try:
                self._stream.start()
            except Exception as e:
                log.warning("Audio stream.start() failed: %s; attempting fallback", e)
                try:
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None
                self._reinit_portaudio()
                fallback_idx = self._find_fallback_device()
                self._open_stream(fallback_idx)
                self._stream.start()

            self.start_time = time.monotonic()

    def stop(self) -> np.ndarray:
        with self._lock:
            stream = self._stream
            self._stream = None
            self.start_time = None
            self._silence_started_at = None

            if stream is not None:
                try:
                    stream.stop()
                    stream.close()
                except Exception as e:
                    log.debug("Stream close ignored: %s", e)

            if not self._buffers:
                return np.empty(0, dtype=np.float32)

            raw = np.concatenate(self._buffers, axis=0)
            self._buffers.clear()

        mono = self._downmix_to_mono(raw)
        return self._resample_to_16k(mono, self._native_sr)

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        if status:
            log.warning("Audio status flag: %s", status)

        chunk = indata.copy()
        with self._lock:
            if self._stream is None:
                return
            self._buffers.append(chunk)

        peak = float(np.max(np.abs(chunk))) if chunk.size else 0.0
        rms = float(np.sqrt(np.mean(chunk**2))) if chunk.size else 0.0

        if self._on_rms:
            try:
                self._on_rms(rms)
            except Exception:
                pass

        now = time.monotonic()
        if peak < SILENCE_PEAK_THRESHOLD:
            if self._silence_started_at is None:
                self._silence_started_at = now
            elif (now - self._silence_started_at) >= SILENCE_DURATION_S:
                self._trigger_silence_fallback()
                self._silence_started_at = now
        else:
            self._silence_started_at = None

        sink = self._preview_sink
        if sink is not None:
            try:
                sink(chunk)
            except Exception:
                pass

    def _open_stream(self, device_idx: Optional[int]) -> None:
        info = (
            sd.query_devices(device_idx, kind="input")
            if device_idx is not None
            else sd.query_devices(kind="input")
        )
        self._device_index = info.get("index") if device_idx is None else device_idx
        self._device_name = str(info.get("name", "unknown"))
        self._native_sr = int(info.get("default_samplerate", TARGET_SR))
        max_ch = int(info.get("max_input_channels", 1))
        self._native_channels = max(1, min(max_ch, 2))

        self._stream = sd.InputStream(
            samplerate=self._native_sr,
            channels=self._native_channels,
            dtype="float32",
            callback=self._audio_callback,
            device=self._device_index,
        )

    def _downmix_to_mono(self, arr: np.ndarray) -> np.ndarray:
        if arr.ndim == 1:
            return arr.astype(np.float32, copy=False)
        if arr.shape[1] == 1:
            return arr[:, 0].astype(np.float32, copy=False)
        return arr.mean(axis=1, dtype=np.float32)

    def _resample_to_16k(self, mono: np.ndarray, orig_sr: int) -> np.ndarray:
        if orig_sr == TARGET_SR:
            return mono
        if mono.size == 0:
            return mono
        from math import gcd
        g = gcd(TARGET_SR, orig_sr)
        up = TARGET_SR // g
        down = orig_sr // g
        resampled = signal.resample_poly(mono, up, down)
        return resampled.astype(np.float32, copy=False)

    def _resolve_target_device(self) -> Optional[int]:
        if self._device_lock is None:
            return None
        idx, name_sub = self._device_lock
        if idx is not None:
            return idx
        if name_sub:
            sub = name_sub.lower()
            try:
                devices = sd.query_devices()
            except Exception:
                return None
            for i, d in enumerate(devices):
                if d.get("max_input_channels", 0) > 0 and sub in d.get("name", "").lower():
                    return i
        return None

    def _find_fallback_device(self) -> Optional[int]:
        try:
            devices = sd.query_devices()
        except Exception:
            return None
        candidates = []
        for i, d in enumerate(devices):
            if d.get("max_input_channels", 0) <= 0:
                continue
            name = d.get("name", "").lower()
            for rank, kw in enumerate(_PreferredBuiltinNames):
                if kw in name:
                    candidates.append((rank, i))
                    break
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        for i, d in enumerate(devices):
            if d.get("max_input_channels", 0) > 0:
                return i
        return None

    def _reinit_portaudio(self) -> None:
        try:
            sd._terminate()
            sd._initialize()
        except Exception as e:
            log.debug("PortAudio reinit issue: %s", e)

    def _trigger_silence_fallback(self) -> None:
        cb = self._silence_callback
        if cb is not None:
            try:
                threading.Thread(target=cb, daemon=True).start()
            except Exception:
                pass
