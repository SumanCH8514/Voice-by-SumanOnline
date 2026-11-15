from __future__ import annotations

import logging
import sys
import threading
from typing import Callable, Optional

log = logging.getLogger("voice_by_sumanonline.tray")

def _make_icon_image(muted: bool = False):
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    accent = (140, 140, 150, 255) if muted else (99, 102, 241, 255)
    draw.rounded_rectangle((24, 12, 40, 38), radius=8, fill=accent)
    draw.line((32, 38, 32, 50), fill=accent, width=3)
    draw.line((22, 50, 42, 50), fill=accent, width=3)
    draw.arc((18, 18, 46, 46), start=200, end=340, fill=accent, width=2)
    return img

if sys.platform == "darwin":
    import objc
    from AppKit import NSImage, NSMenu, NSMenuItem, NSStatusBar, NSStatusItem
    from Foundation import NSObject

    class _MacosTrayDelegate(NSObject):
        def initWithCallbacks_(self, callbacks):
            self = objc.super(_MacosTrayDelegate, self).init()
            if self is None:
                return None
            self._callbacks = callbacks
            return self

        @objc.python_method
        def _safe(self, fn, *args):
            try:
                fn(*args)
            except Exception:
                log.exception("Tray callback failed.")

        def openSettings_(self, _sender):
            self._safe(self._callbacks["on_settings"])

        def quitApp_(self, _sender):
            self._safe(self._callbacks["on_quit"])

        def toggleMute_(self, _sender):
            self._safe(self._callbacks["on_toggle_mute"])

    class TrayController:
        def __init__(
            self,
            *,
            on_settings: Callable[[], None],
            on_quit: Callable[[], None],
            on_toggle_mute: Callable[[], None],
            initial_muted: bool = False,
        ) -> None:
            self._callbacks = {
                "on_settings": on_settings,
                "on_quit": on_quit,
                "on_toggle_mute": on_toggle_mute,
            }
            self._muted = initial_muted
            self._status_item: Optional[NSStatusItem] = None
            self._delegate: Optional[_MacosTrayDelegate] = None

        def start(self) -> None:
            if threading.current_thread() is not threading.main_thread():
                return
            sb = NSStatusBar.systemStatusBar()
            self._status_item = sb.statusItemWithLength_(-1)
            self._delegate = _MacosTrayDelegate.alloc().initWithCallbacks_(self._callbacks)
            self._build_menu()
            self._update_title()

        def stop(self) -> None:
            if self._status_item is not None:
                sb = NSStatusBar.systemStatusBar()
                sb.removeStatusItem_(self._status_item)
                self._status_item = None

        def set_muted(self, muted: bool) -> None:
            self._muted = muted
            self._update_title()
            self._build_menu()

        def _update_title(self) -> None:
            if self._status_item is None:
                return
            btn = self._status_item.button()
            if btn is not None:
                btn.setTitle_("🔇" if self._muted else "🎙")

        def _build_menu(self) -> None:
            if self._status_item is None or self._delegate is None:
                return
            menu = NSMenu.alloc().init()
            title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Voice by SumanOnline", None, ""
            )
            title.setEnabled_(False)
            menu.addItem_(title)
            menu.addItem_(NSMenuItem.separatorItem())

            settings_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Open Voice Studio...", "openSettings:", ","
            )
            settings_item.setTarget_(self._delegate)
            menu.addItem_(settings_item)

            mute_title = "Unmute Dictation" if self._muted else "Quick Mute"
            mute_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                mute_title, "toggleMute:", "m"
            )
            mute_item.setTarget_(self._delegate)
            menu.addItem_(mute_item)

            menu.addItem_(NSMenuItem.separatorItem())
            quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Quit Voice by SumanOnline", "quitApp:", "q"
            )
            quit_item.setTarget_(self._delegate)
            menu.addItem_(quit_item)

            self._status_item.setMenu_(menu)

else:
    class TrayController:
        def __init__(
            self,
            *,
            on_settings: Callable[[], None],
            on_quit: Callable[[], None],
            on_toggle_mute: Callable[[], None],
            initial_muted: bool = False,
        ) -> None:
            self._on_settings = on_settings
            self._on_quit = on_quit
            self._on_toggle_mute = on_toggle_mute
            self._muted = initial_muted
            self._icon = None
            self._thread: Optional[threading.Thread] = None

        def start(self) -> None:
            try:
                import pystray
            except ImportError:
                log.warning("pystray not installed; running headless.")
                return

            menu = self._build_menu()
            image = _make_icon_image(self._muted)
            self._icon = pystray.Icon(
                "voice_by_sumanonline",
                image,
                "Voice by SumanOnline",
                menu=menu,
            )
            self._thread = threading.Thread(
                target=self._run,
                name="TrayThread",
                daemon=True,
            )
            self._thread.start()

        def stop(self) -> None:
            if self._icon is not None:
                try:
                    self._icon.stop()
                except Exception:
                    pass
                self._icon = None

        def set_muted(self, muted: bool) -> None:
            self._muted = muted
            if self._icon is not None:
                try:
                    self._icon.icon = _make_icon_image(muted)
                    self._icon.menu = self._build_menu()
                except Exception:
                    pass

        def _run(self) -> None:
            if self._icon is None:
                return
            try:
                self._icon.run()
            except Exception as e:
                log.warning("Tray run ended: %s", e)

        def _build_menu(self):
            import pystray

            def _action(fn):
                def _wrapped(icon, item):
                    try:
                        fn()
                    except Exception:
                        log.exception("Tray action failed.")
                return _wrapped

            mute_label = "Unmute Dictation" if self._muted else "Quick Mute"

            return pystray.Menu(
                pystray.MenuItem("Voice by SumanOnline", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Open Voice Studio...", _action(self._on_settings), default=True),
                pystray.MenuItem(mute_label, _action(self._on_toggle_mute)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", _action(self._on_quit)),
            )
