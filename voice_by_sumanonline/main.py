from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SumanOnline.Voice.Desktop.1")
except Exception:
    pass

from dotenv import load_dotenv

import numpy as np
import sounddevice as sd
import uvicorn

load_dotenv()

from .audio import Recorder
from .config import CONFIG_PATH, get_dictionary, load_config, save_config
from .dictionary import apply_dictionary, compile_dictionary
from .format import clean_transcript
from .history import record_dictation
from .hotkey import PushToTalk
from .hud import HUD
from .inject import accessibility_hint, inject_text, is_trusted
from .keychain import get_api_key, set_api_key
from .preview import StreamingPreview
from .server import app as fastapi_app, set_engine_state_callback, set_latest_dictation, ws_manager
from .startup import disable as startup_disable, enable as startup_enable, is_enabled as startup_is_enabled
from .transcribe import set_model_name, transcribe
from .tray import TrayController

log = logging.getLogger("voice_by_sumanonline")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

class AppState:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.muted = False
        self.lock = threading.Lock()
        self._recorder: Optional[Recorder] = None
        self._ptt: Optional[PushToTalk] = None
        self._hud: Optional[HUD] = None
        self._tray: Optional[TrayController] = None
        self._preview: Optional[StreamingPreview] = None
        self.is_recording = False
        self.is_processing = False

    def set_recorder(self, recorder: Recorder) -> None:
        self._recorder = recorder

    def set_ptt(self, ptt: PushToTalk) -> None:
        self._ptt = ptt

    def set_hud(self, hud: HUD) -> None:
        self._hud = hud

    def set_tray(self, tray: TrayController) -> None:
        self._tray = tray

    def set_preview(self, preview: StreamingPreview) -> None:
        self._preview = preview

_GLOBAL_APP_STATE: Optional[AppState] = None

def get_global_app_state() -> Optional[AppState]:
    return _GLOBAL_APP_STATE

def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="voice-by-sumanonline",
        description="Voice by SumanOnline — push-to-talk and hands-free AI voice dictation desktop app.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Lock the recorder to a specific input device (index or name substring).",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit.",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Open the Voice Studio desktop interface in browser on launch.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help=f"Override path to config.json (default: {CONFIG_PATH}).",
    )
    return parser.parse_args(argv)

def cmd_list_devices() -> int:
    print("Available input devices:")
    try:
        devices = sd.query_devices()
    except Exception as e:
        print(f"  (could not query devices: {e})")
        return 1
    for i, d in enumerate(devices):
        if d.get("max_input_channels", 0) > 0:
            sr = int(d.get("default_samplerate", 0))
            print(f"  #{i}: {d.get('name', '?')} ({sr} Hz)")
    print()
    try:
        default = sd.query_devices(kind="input")
        print(f"Default input: #{default.get('index')} — {default.get('name')}")
    except Exception:
        pass
    return 0

def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

def _select_input_device() -> None:
    try:
        dev = sd.query_devices(kind="input")
        idx = dev.get("index", "?")
        name = dev.get("name", "default input")
        sr = int(dev.get("default_samplerate", 16000))
        ch = int(dev.get("max_input_channels", 1))
        log.info(
            "Selected input device #%s: %s (%d Hz, %d ch max)",
            idx, name, sr, ch,
        )
    except Exception as e:
        log.warning("Could not query default input device: %s", e)

def apply_live_config(cfg: Dict[str, Any]) -> None:
    global _GLOBAL_APP_STATE
    if not _GLOBAL_APP_STATE:
        return
    app = _GLOBAL_APP_STATE
    model = cfg.get("transcription", {}).get("model", "base")
    set_model_name(model)

    if app._recorder:
        dev = cfg.get("input_device")
        if isinstance(dev, int):
            app._recorder.lock_device(index=dev)
        elif isinstance(dev, str) and dev:
            app._recorder.lock_device(name_substring=dev)
        else:
            app._recorder.lock_device(index=None, name_substring=None)

    if app._ptt:
        if "hotkey" in cfg:
            app._ptt.set_key(cfg["hotkey"])
        if "toggle_mode" in cfg:
            app._ptt.set_toggle_mode(bool(cfg["toggle_mode"]))

    want = bool(cfg.get("start_on_login", False))
    currently = startup_is_enabled()
    if want and not currently:
        startup_enable()
    elif not want and currently:
        startup_disable()

    with app.lock:
        if isinstance(app.config, dict) and app.config is not cfg:
            app.config.clear()
            app.config.update(cfg)
        else:
            app.config = cfg

def manual_trigger_dictation() -> str:
    global _GLOBAL_APP_STATE
    if not _GLOBAL_APP_STATE or not _GLOBAL_APP_STATE._ptt:
        return "idle"
    app = _GLOBAL_APP_STATE
    if not app.is_recording:
        app._ptt.force_start_latched()
        return "recording"
    else:
        app._ptt.force_stop()
        return "processing"

def toggle_global_mute() -> bool:
    global _GLOBAL_APP_STATE
    if not _GLOBAL_APP_STATE:
        return False
    app = _GLOBAL_APP_STATE
    with app.lock:
        app.muted = not app.muted
        muted = app.muted
    if app._tray:
        app._tray.set_muted(muted)
    ws_manager.threadsafe_broadcast({"type": "mute_changed", "muted": muted})
    return muted

def _run_finalize(
    audio: np.ndarray,
    hud: Any,
    config: Any = None,
    api_key: Optional[str] = None,
    audio_duration_s: float = 0.0,
    release_monotonic: float = 0.0,
    inject_fn: Optional[Callable[[str], None]] = None,
) -> None:
    if config is None:
        config = {}
    if release_monotonic == 0.0:
        release_monotonic = time.monotonic()
    release_ts = release_monotonic

    try:
        log.info("Transcribing audio buffer...")
        t_w0 = time.monotonic()
        try:
            raw = transcribe(audio)
        except Exception:
            log.exception("Transcription failed.")
            return
        t_w1 = time.monotonic()
        whisper_s = t_w1 - t_w0

        if not raw:
            log.info("Empty transcript.")
            ws_manager.threadsafe_broadcast({"type": "transcript_empty"})
            return

        log.info("Raw transcript: %r", raw)
        ws_manager.threadsafe_broadcast({
            "type": "raw_transcript",
            "text": raw,
            "whisper_latency_s": round(whisper_s, 2),
        })

        fmt_cfg = config.get("format", {})
        t_f0 = time.monotonic()
        preset = config.get("style_preset", "smart")
        custom_prompt = config.get("custom_prompt", "")
        try:
            result = clean_transcript(
                raw,
                groq_api_key=api_key,
                groq_model=fmt_cfg.get("groq_model", "qwen/qwen3.8-27b"),
                ollama_model=fmt_cfg.get("ollama_model", "llama3.2:3b"),
                tier_override=fmt_cfg.get("tier", "auto"),
                dictionary=get_dictionary(config),
                style_preset=preset,
                custom_prompt=custom_prompt,
            )
        except Exception:
            log.exception("Cleanup failed; using raw transcript.")
            cleaned = raw
            tier_label = "raw"
            format_s = 0.0
        else:
            cleaned = result.text
            tier_label = result.tier
            format_s = time.monotonic() - t_f0
            log.info("Cleaned (%s): %r", tier_label, cleaned)

        total_latency = time.monotonic() - release_ts

        record_dictation(
            raw_text=raw,
            cleaned_text=cleaned,
            preset=preset,
            tier=tier_label,
            audio_duration_s=audio_duration_s,
            latency_s=total_latency,
            whisper_s=whisper_s,
            format_s=format_s,
        )

        dictation_payload = {
            "raw": raw,
            "cleaned": cleaned,
            "tier": tier_label,
            "preset": preset,
            "latency_s": round(total_latency, 2),
            "whisper_s": round(whisper_s, 2),
            "format_s": round(format_s, 2),
            "audio_duration_s": round(audio_duration_s, 2),
        }
        set_latest_dictation(dictation_payload)
        ws_manager.threadsafe_broadcast({
            "type": "final_result",
            **dictation_payload,
        })

        stats = config.setdefault("stats", {})
        stats["total_dictations"] = int(stats.get("total_dictations", 0)) + 1
        stats["total_words"] = int(stats.get("total_words", 0)) + len(cleaned.split())
        stats["total_seconds_recorded"] = float(stats.get("total_seconds_recorded", 0.0)) + audio_duration_s

        try:
            if inject_fn is not None:
                injected = inject_fn(cleaned)
            else:
                injected = inject_text(cleaned)
            if injected is False:
                log.warning("Injection returned False.")
        except Exception:
            log.exception("Injection failed.")
            return

    finally:
        if hud:
            hud.hide()
        ws_manager.threadsafe_broadcast({"type": "state_changed", "state": "idle"})
        global _GLOBAL_APP_STATE
        if _GLOBAL_APP_STATE:
            _GLOBAL_APP_STATE.is_recording = False
            _GLOBAL_APP_STATE.is_processing = False

def _start_server(port: int = 48922) -> None:
    def _run():
        try:
            uvicorn.run(fastapi_app, host="127.0.0.1", port=port, log_config=None)
        except Exception as e:
            log.exception("Server failed to start on port %s: %s", port, e)

    thread = threading.Thread(target=_run, name="VoiceStudioServer", daemon=True)
    thread.start()

def _wait_for_server(port: int = 48922, timeout: float = 8.0) -> bool:
    import socket
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.05)
    return False

def main(argv: Optional[list] = None) -> int:
    _setup_logging()
    args = parse_args(argv)

    if args.list_devices:
        return cmd_list_devices()

    if not is_trusted(prompt=True):
        print(
            "Accessibility permission required for cursor text injection.",
            file=sys.stderr,
        )
        print(f"Grant permission to: {accessibility_hint()}", file=sys.stderr)

    config_path = Path(args.config) if args.config else CONFIG_PATH
    config = load_config(config_path)

    global _GLOBAL_APP_STATE
    app_state = AppState(config)
    _GLOBAL_APP_STATE = app_state

    set_engine_state_callback(lambda: {
        "is_recording": app_state.is_recording,
        "is_processing": app_state.is_processing,
        "muted": app_state.muted,
        "hotkey": config.get("hotkey", "Key.alt_r"),
        "toggle_mode": config.get("toggle_mode", False),
    })

    model_name = config.get("transcription", {}).get("model", "base")
    set_model_name(model_name)

    server_port = int(config.get("server", {}).get("port", 48922))
    _start_server(port=server_port)

    recent_rms: List[float] = [0.0] * 5
    rms_lock = threading.Lock()

    def rms_provider(n: int = 5) -> List[float]:
        with rms_lock:
            return list(recent_rms)

    def on_live_rms(val: float) -> None:
        with rms_lock:
            recent_rms.pop(0)
            recent_rms.append(val)
        ws_manager.threadsafe_broadcast({
            "type": "audio_rms",
            "rms": round(val, 4),
            "rms_bars": list(recent_rms),
        })

    recorder = Recorder(on_rms=on_live_rms)
    app_state.set_recorder(recorder)

    if args.device is not None:
        try:
            idx = int(args.device)
            recorder.lock_device(index=idx)
        except ValueError:
            recorder.lock_device(name_substring=args.device)
    else:
        dev = config.get("input_device")
        if isinstance(dev, int):
            recorder.lock_device(index=dev)
        elif isinstance(dev, str) and dev:
            recorder.lock_device(name_substring=dev)

    _select_input_device()

    hud = HUD(rms_provider=rms_provider)
    app_state.set_hud(hud)

    streaming_preview = StreamingPreview()
    preview_enabled = bool(config.get("transcription", {}).get("preview_enabled", True))
    if preview_enabled:
        threading.Thread(target=streaming_preview.initialize, daemon=True, name="VoskInit").start()
    app_state.set_preview(streaming_preview)

    def on_preview_text(txt: str) -> None:
        hud.set_preview_text(txt)
        ws_manager.threadsafe_broadcast({"type": "preview_text", "text": txt})

    streaming_preview.set_on_partial(on_preview_text)
    recorder.set_preview_sink(streaming_preview.feed_audio)

    finalize_thread: Optional[threading.Thread] = None
    release_ts: float = 0.0

    def on_press() -> None:
        nonlocal release_ts
        with app_state.lock:
            if app_state.muted:
                log.info("Dictation is muted.")
                return
            app_state.is_recording = True
            app_state.is_processing = False

        log.info("Recording started.")
        ws_manager.threadsafe_broadcast({"type": "state_changed", "state": "recording"})

        streaming_preview.configure_input_rate(recorder.native_sample_rate)
        streaming_preview.start()
        recorder.start()

        overlay_enabled = bool(app_state.config.get("overlay_enabled", True))
        if overlay_enabled:
            hud.show_recording(preview_active=streaming_preview.is_ready())

    def on_release() -> None:
        nonlocal finalize_thread, release_ts
        with app_state.lock:
            if not app_state.is_recording:
                return
            app_state.is_recording = False
            app_state.is_processing = True

        release_ts = time.monotonic()
        ws_manager.threadsafe_broadcast({"type": "state_changed", "state": "processing"})

        audio = recorder.stop()
        streaming_preview.stop()

        overlay_enabled = bool(app_state.config.get("overlay_enabled", True))
        if overlay_enabled:
            hud.show_processing()

        audio_s = float(len(audio)) / 16000.0 if audio is not None and len(audio) else 0.0

        if audio_s < 0.30:
            log.info("Audio too short (%.2fs); discarded.", audio_s)
            hud.hide()
            with app_state.lock:
                app_state.is_processing = False
            ws_manager.threadsafe_broadcast({"type": "state_changed", "state": "idle"})
            return

        api_key = get_api_key()

        finalize_thread = threading.Thread(
            target=_run_finalize,
            args=(audio, hud, app_state.config, api_key, audio_s, release_ts),
            name="FinalizeThread",
            daemon=True,
        )
        finalize_thread.start()

    hotkey_spec = config.get("hotkey", "Key.alt_r")
    toggle_mode = bool(config.get("toggle_mode", False))
    ptt = PushToTalk(
        on_press=on_press,
        on_release=on_release,
        key=hotkey_spec,
        toggle_mode=toggle_mode,
    )
    app_state.set_ptt(ptt)
    ptt.start()

    native_win = None
    quitting = False

    def on_open_studio() -> None:
        nonlocal native_win
        if native_win is not None:
            try:
                native_win.show()
                native_win.restore()
                return
            except Exception:
                pass
        url = f"http://127.0.0.1:{server_port}"
        webbrowser.open(url)

    def on_closing():
        nonlocal native_win, quitting
        if quitting:
            return True
        if native_win is not None:
            try:
                native_win.hide()
            except Exception:
                pass
        return False

    def on_quit() -> None:
        nonlocal quitting, native_win
        quitting = True
        log.info("Quitting Voice by SumanOnline...")
        try:
            save_config(app_state.config, config_path)
        except Exception:
            pass
        ptt.stop()
        recorder.stop()
        streaming_preview.stop()
        hud.close()
        if app_state._tray:
            app_state._tray.stop()
        if native_win is not None:
            try:
                native_win.events.closing -= on_closing
                native_win.destroy()
            except Exception:
                pass
        os._exit(0)

    tray = TrayController(
        on_settings=on_open_studio,
        on_quit=on_quit,
        on_toggle_mute=toggle_global_mute,
        initial_muted=app_state.muted,
    )
    app_state.set_tray(tray)
    tray.start()

    log.info("Voice by SumanOnline is running. Push-to-talk key: %s", hotkey_spec)
    log.info("Voice Studio URL: http://127.0.0.1:%d", server_port)

    hud_thread = threading.Thread(target=hud.run, name="HudThread", daemon=True)
    hud_thread.start()

    _wait_for_server(server_port, timeout=8.0)
    url = f"http://127.0.0.1:{server_port}"
    try:
        import webview
        show_window = bool(args.ui)
        native_win = webview.create_window(
            "Voice by SumanOnline",
            url=url,
            width=1160,
            height=760,
            min_size=(900, 620),
            background_color="#080C14",
            hidden=not show_window,
        )
        native_win.events.closing += on_closing

        def _apply_window_icon():
            try:
                import ctypes
                icon_file = _PROJECT_ROOT / "assets" / "logo.ico"
                if not icon_file.exists():
                    icon_file = Path(sys.executable).parent.parent / "assets" / "logo.ico"
                if icon_file.exists():
                    hwnd = ctypes.windll.user32.FindWindowW(None, "Voice by SumanOnline")
                    if hwnd:
                        hicon = ctypes.windll.user32.LoadImageW(None, str(icon_file), 1, 0, 0, 0x00000010 | 0x00000040)
                        if hicon:
                            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon)
                            ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon)
            except Exception:
                pass

        native_win.events.shown += _apply_window_icon
        webview.start()
    except Exception as e:
        log.warning("pywebview failed (%s); running headless with browser support", e)
        if args.ui:
            on_open_studio()
        hud_thread.join()

    return 0

if __name__ == "__main__":
    sys.exit(main())
