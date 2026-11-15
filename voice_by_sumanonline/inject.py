from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import time
from typing import List, Optional

from pynput.keyboard import Controller, Key

from ._platform import is_wayland_session

log = logging.getLogger("voice_by_sumanonline.inject")

_kb = Controller()

def is_trusted(prompt: bool = False) -> bool:
    if sys.platform != "darwin":
        return True
    try:
        if prompt:
            from HIServices import AXIsProcessTrustedWithOptions
            return bool(AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True}))
        from ApplicationServices import AXIsProcessTrusted
        return bool(AXIsProcessTrusted())
    except Exception:
        return True

def accessibility_hint() -> str:
    import os
    exe = os.path.realpath(sys.executable)
    term = os.environ.get("TERM_PROGRAM") or os.environ.get("__CFBundleIdentifier")
    if term:
        return f"your application/terminal ({term}) — or {exe}"
    return f"your application or terminal ({exe})"

def _read_clipboard() -> Optional[str]:
    if sys.platform == "darwin":
        try:
            out = subprocess.run(
                ["pbpaste", "-Prefer", "ascii"],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            ).stdout
            return out
        except Exception:
            return None

    if sys.platform == "win32":
        try:
            import win32clipboard

            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    return data
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            return None
        return None

    if is_wayland_session():
        if shutil.which("wl-paste"):
            try:
                r = subprocess.run(
                    ["wl-paste", "--no-newline"],
                    capture_output=True,
                    text=True,
                    timeout=1.0,
                    check=False,
                )
                if r.returncode == 0:
                    return r.stdout
            except Exception:
                pass
        return None

    for cmd in (["xclip", "-selection", "clipboard", "-o"], ["xsel", "--clipboard", "--output"]):
        if shutil.which(cmd[0]):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=1.0, check=False)
                if r.returncode == 0:
                    return r.stdout
            except Exception:
                pass
    return None

def _write_clipboard(text: str) -> bool:
    if sys.platform == "darwin":
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            p.communicate(text.encode("utf-8"), timeout=1.0)
            return p.returncode == 0
        except Exception:
            return False

    if sys.platform == "win32":
        for attempt in range(5):
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
                    return True
                finally:
                    win32clipboard.CloseClipboard()
            except Exception:
                time.sleep(0.01 * (attempt + 1))
        return False

    if is_wayland_session():
        if shutil.which("wl-copy"):
            try:
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                p.communicate(text.encode("utf-8"), timeout=1.0)
                return p.returncode == 0
            except Exception:
                pass

    for tool in ("xclip", "xsel"):
        if shutil.which(tool):
            cmd = [tool, "-selection", "clipboard"] if tool == "xclip" else [tool, "--clipboard", "--input"]
            try:
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                p.communicate(text.encode("utf-8"), timeout=1.0)
                return p.returncode == 0
            except Exception:
                pass
    return False

def _send_paste_shortcut() -> None:
    if sys.platform == "darwin":
        _kb.press(Key.cmd)
        _kb.press("v")
        time.sleep(0.01)
        _kb.release("v")
        _kb.release(Key.cmd)
        return

    if is_wayland_session():
        if shutil.which("wtype"):
            try:
                res = subprocess.run(["wtype", "-M", "ctrl", "v", "-m", "ctrl"], check=False)
                if res.returncode == 0:
                    return
            except Exception:
                pass
        if shutil.which("ydotool"):
            try:
                res = subprocess.run(["ydotool", "key", "29:1", "47:1", "47:0", "29:0"], check=False)
                if res.returncode == 0:
                    return
            except Exception:
                pass

    _kb.press(Key.ctrl)
    _kb.press("v")
    time.sleep(0.01)
    _kb.release("v")
    _kb.release(Key.ctrl)

def inject_text(text: str, restore_delay_s: float = 0.45) -> bool:
    if not text:
        return False

    old_clip = _read_clipboard()

    if not _write_clipboard(text):
        return False

    time.sleep(0.02)
    _send_paste_shortcut()

    if old_clip is not None:
        def _restore() -> None:
            time.sleep(restore_delay_s)
            _write_clipboard(old_clip)

        import threading
        threading.Thread(target=_restore, daemon=True).start()

    return True
