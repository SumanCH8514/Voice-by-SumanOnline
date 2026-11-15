from __future__ import annotations

import logging
import os
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from pynput import keyboard

log = logging.getLogger("voice_by_sumanonline.hotkey")

class PushToTalk:
    def __init__(
        self,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        key: Optional[Any] = None,
        toggle_mode: bool = False,
        double_tap_interval: float = 0.40,
    ) -> None:
        self._on_press = on_press
        self._on_release = on_release
        self._key_spec = str(key) if key else "Key.alt_r"
        self._key = self._resolve_key(key or keyboard.Key.alt_r)
        self._held = False
        self._toggle_mode = toggle_mode
        self._is_recording_toggle = False
        self._double_tap_interval = double_tap_interval
        self._press_time = 0.0
        self._waiting_for_second_tap = False
        self._is_latched = False
        self._just_unlatched = False
        self._tap_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._listener: Optional[Any] = None

    @property
    def key(self) -> keyboard.Key:
        return self._key

    @property
    def key_spec(self) -> str:
        return self._key_spec

    @property
    def toggle_mode(self) -> bool:
        return self._toggle_mode

    @property
    def is_latched(self) -> bool:
        with self._lock:
            return self._is_latched

    def set_toggle_mode(self, enabled: bool) -> None:
        with self._lock:
            self._toggle_mode = enabled
            self._is_recording_toggle = False
            self._held = False

    def set_key(self, key_spec: Any) -> None:
        new_key = self._resolve_key(key_spec)
        with self._lock:
            self._key_spec = str(key_spec)
            if self._key == new_key:
                return
            self._key = new_key
            self._held = False
            self._is_recording_toggle = False

    @staticmethod
    def _resolve_key(key_spec: Any) -> keyboard.Key:
        if isinstance(key_spec, keyboard.Key):
            return key_spec
        if isinstance(key_spec, str):
            clean = key_spec.strip()
            if clean.startswith("Key."):
                clean = clean[4:]
            aliases = {
                "ctrl_l": "ctrl",
                "alt_l": "alt",
                "cmd_l": "cmd",
                "shift_l": "shift",
            }
            clean = aliases.get(clean, clean)
            try:
                return getattr(keyboard.Key, clean)
            except AttributeError:
                pass
        return keyboard.Key.alt_r

    def start(self) -> None:
        if self._listener is not None:
            return
        if _want_evdev():
            try:
                self._listener = _EvdevListener(
                    on_press=self._handle_press,
                    on_release=self._handle_release,
                )
                self._listener.start()
                return
            except Exception as e:
                log.warning("evdev failed (%s); falling back to pynput", e)

        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def _cancel_tap_timer_locked(self) -> None:
        if self._tap_timer is not None:
            try:
                self._tap_timer.cancel()
            except Exception:
                pass
            self._tap_timer = None

    def force_start_latched(self) -> None:
        with self._lock:
            self._cancel_tap_timer_locked()
            self._waiting_for_second_tap = False
            self._is_latched = True
            self._held = False
        try:
            self._on_press()
        except Exception as e:
            log.exception("force_start_latched failed: %s", e)

    def force_stop(self) -> None:
        with self._lock:
            self._cancel_tap_timer_locked()
            self._waiting_for_second_tap = False
            self._is_latched = False
            self._held = False
        try:
            self._on_release()
        except Exception as e:
            log.exception("force_stop failed: %s", e)

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        with self._lock:
            self._cancel_tap_timer_locked()
            self._held = False
            self._waiting_for_second_tap = False
            self._is_latched = False
            self._is_recording_toggle = False

    def _matches_target(self, key: Any) -> bool:
        if key == self._key:
            return True
        if self._key == keyboard.Key.alt_r and key == keyboard.Key.alt_gr:
            return True
        if self._key == keyboard.Key.alt_gr and key == keyboard.Key.alt_r:
            return True
        return False

    def _on_key_press(self, key: Any) -> None:
        if self._matches_target(key):
            self._handle_press()

    def _on_key_release(self, key: Any) -> None:
        if self._matches_target(key):
            self._handle_release()

    def _handle_press(self) -> None:
        trigger_start = False
        trigger_stop = False

        with self._lock:
            now = time.monotonic()
            if self._toggle_mode:
                if not self._is_recording_toggle:
                    self._is_recording_toggle = True
                    trigger_start = True
                else:
                    self._is_recording_toggle = False
                    trigger_stop = True
            else:
                if self._held:
                    return
                self._held = True
                self._press_time = now

                if self._is_latched:
                    self._is_latched = False
                    self._just_unlatched = True
                    trigger_stop = True
                elif self._waiting_for_second_tap:
                    self._cancel_tap_timer_locked()
                    self._waiting_for_second_tap = False
                    self._is_latched = True
                else:
                    trigger_start = True

        if trigger_start:
            try:
                self._on_press()
            except Exception as e:
                log.exception("on_press failed: %s", e)
        elif trigger_stop:
            try:
                self._on_release()
            except Exception as e:
                log.exception("on_release failed: %s", e)

    def _handle_release(self) -> None:
        trigger_stop = False

        with self._lock:
            if self._toggle_mode:
                return
            if not self._held:
                return
            self._held = False

            if self._just_unlatched:
                self._just_unlatched = False
                return

            if self._is_latched:
                return

            duration = time.monotonic() - self._press_time
            if duration < self._double_tap_interval:
                self._waiting_for_second_tap = True
                self._cancel_tap_timer_locked()
                self._tap_timer = threading.Timer(
                    self._double_tap_interval,
                    self._on_single_tap_timeout,
                )
                self._tap_timer.daemon = True
                self._tap_timer.start()
                return
            else:
                trigger_stop = True

        if trigger_stop:
            try:
                self._on_release()
            except Exception as e:
                log.exception("on_release failed: %s", e)

    def _on_single_tap_timeout(self) -> None:
        trigger_stop = False
        with self._lock:
            if self._waiting_for_second_tap and not self._is_latched:
                self._waiting_for_second_tap = False
                trigger_stop = True
        if trigger_stop:
            try:
                self._on_release()
            except Exception as e:
                log.exception("on_release failed on tap timeout: %s", e)

def _want_evdev() -> bool:
    if os.environ.get("VOICE_HOTKEY_BACKEND") == "evdev":
        return True
    if os.environ.get("VOICE_HOTKEY_BACKEND") == "pynput":
        return False
    if not (sys.platform.startswith("linux") or "bsd" in sys.platform):
        return False
    from ._platform import is_wayland_session
    return is_wayland_session()

class _EvdevListener:
    def __init__(self, on_press: Callable[[], None], on_release: Callable[[], None]) -> None:
        self._on_press = on_press
        self._on_release = on_release
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        import evdev
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="EvdevListener", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        import evdev
        import select

        keyboards = []
        for path in evdev.list_devices():
            try:
                dev = evdev.InputDevice(path)
                caps = dev.capabilities()
                if evdev.ecodes.EV_KEY in caps:
                    keys = caps[evdev.ecodes.EV_KEY]
                    if evdev.ecodes.KEY_RIGHTALT in keys or evdev.ecodes.KEY_LEFTALT in keys:
                        keyboards.append(dev)
            except Exception:
                continue

        if not keyboards:
            return

        while not self._stop_event.is_set():
            try:
                r, _, _ = select.select(keyboards, [], [], 0.2)
                for dev in r:
                    for ev in dev.read():
                        if ev.type == evdev.ecodes.EV_KEY and ev.code in (evdev.ecodes.KEY_RIGHTALT, evdev.ecodes.KEY_LEFTALT):
                            if ev.value == 1:
                                self._on_press()
                            elif ev.value == 0:
                                self._on_release()
            except Exception:
                pass
