from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

log = logging.getLogger("voice_by_sumanonline.startup")

SERVICE_ID = "com.sumanonline.voice"
DISPLAY_NAME = "VoiceBySumanOnline"

def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent

def _is_linux() -> bool:
    return sys.platform.startswith("linux") or "bsd" in sys.platform

def is_enabled() -> bool:
    if sys.platform == "darwin":
        return _macos_plist_path().exists()
    if sys.platform == "win32":
        return _windows_registry_value_exists()
    if _is_linux():
        return _linux_desktop_path().exists()
    return False

def enable() -> bool:
    try:
        if sys.platform == "darwin":
            _enable_macos()
        elif sys.platform == "win32":
            _enable_windows()
        elif _is_linux():
            _enable_linux()
        else:
            return False
        return True
    except Exception as e:
        log.exception("Failed to enable start-on-login: %s", e)
        return False

def disable() -> bool:
    try:
        if sys.platform == "darwin":
            _disable_macos()
        elif sys.platform == "win32":
            _disable_windows()
        elif _is_linux():
            _disable_linux()
        return True
    except Exception as e:
        log.exception("Failed to disable start-on-login: %s", e)
        return False

def _macos_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{SERVICE_ID}.plist"

def _enable_macos() -> None:
    plist = _macos_plist_path()
    plist.parent.mkdir(parents=True, exist_ok=True)
    exe = sys.executable
    script = _project_root() / "voice_by_sumanonline" / "main.py"
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{SERVICE_ID}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe}</string>
        <string>{script}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>WorkingDirectory</key>
    <string>{_project_root()}</string>
</dict>
</plist>
"""
    plist.write_text(content, encoding="utf-8")

def _disable_macos() -> None:
    plist = _macos_plist_path()
    if plist.exists():
        plist.unlink()

def _windows_run_key():
    import winreg
    return winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_ALL_ACCESS,
    )

def _windows_registry_value_exists() -> bool:
    import winreg
    try:
        with _windows_run_key() as key:
            val, _ = winreg.QueryValueEx(key, DISPLAY_NAME)
            return bool(val)
    except FileNotFoundError:
        return False
    except OSError:
        return False

def _enable_windows() -> None:
    import winreg
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    exe = str(pythonw if pythonw.exists() else sys.executable)
    cmd = f'"{exe}" -m voice_by_sumanonline.main'
    with _windows_run_key() as key:
        winreg.SetValueEx(key, DISPLAY_NAME, 0, winreg.REG_SZ, cmd)

def _disable_windows() -> None:
    import winreg
    try:
        with _windows_run_key() as key:
            winreg.DeleteValue(key, DISPLAY_NAME)
    except FileNotFoundError:
        pass

def _linux_desktop_path() -> Path:
    return Path.home() / ".config" / "autostart" / "voice_by_sumanonline.desktop"

def _enable_linux() -> None:
    desk = _linux_desktop_path()
    desk.parent.mkdir(parents=True, exist_ok=True)
    exe = sys.executable
    script = _project_root() / "voice_by_sumanonline" / "main.py"
    content = f"""[Desktop Entry]
Type=Application
Exec={exe} {script}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Voice by SumanOnline
Comment=Push-to-talk voice dictation desktop app
Path={_project_root()}
"""
    desk.write_text(content, encoding="utf-8")

def _disable_linux() -> None:
    desk = _linux_desktop_path()
    if desk.exists():
        desk.unlink()
