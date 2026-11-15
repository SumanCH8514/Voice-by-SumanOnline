from __future__ import annotations

import logging
import math
import queue
import sys
import threading
import time
from typing import Callable, List, Optional, Protocol

log = logging.getLogger("voice_by_sumanonline.hud")

class _HUDImpl(Protocol):
    def show_recording(self, preview_active: bool) -> None: ...
    def show_processing(self) -> None: ...
    def hide(self) -> None: ...
    def set_preview_text(self, text: str) -> None: ...
    def set_status_text(self, text: str) -> None: ...
    def run(self) -> None: ...
    def close(self) -> None: ...

class HUD:
    WIDTH_COLLAPSED = 160
    HEIGHT_COLLAPSED = 48
    WIDTH_EXPANDED = 460
    HEIGHT_EXPANDED = 96
    FADE_SECONDS = 0.15
    SIZE_SECONDS = 0.22
    BOTTOM_MARGIN = 80
    EXPANDED_LAYOUT_THRESHOLD = 70

    def __init__(
        self,
        rms_provider: Optional[Callable[[int], List[float]]] = None,
    ) -> None:
        self._rms_provider = rms_provider
        if sys.platform == "darwin":
            self._impl: _HUDImpl = _MacOSHUD(
                rms_provider,
                w_collapsed=self.WIDTH_COLLAPSED,
                h_collapsed=self.HEIGHT_COLLAPSED,
                w_expanded=self.WIDTH_EXPANDED,
                h_expanded=self.HEIGHT_EXPANDED,
                bottom_margin=self.BOTTOM_MARGIN,
                fade_seconds=self.FADE_SECONDS,
                size_seconds=self.SIZE_SECONDS,
            )
        else:
            self._impl = _TkHUD(
                rms_provider,
                w_collapsed=self.WIDTH_COLLAPSED,
                h_collapsed=self.HEIGHT_COLLAPSED,
                w_expanded=self.WIDTH_EXPANDED,
                h_expanded=self.HEIGHT_EXPANDED,
                bottom_margin=self.BOTTOM_MARGIN,
                fade_seconds=self.FADE_SECONDS,
                size_seconds=self.SIZE_SECONDS,
            )

    def show_recording(self, preview_active: bool = True) -> None:
        self._impl.show_recording(preview_active)

    def show_processing(self) -> None:
        self._impl.show_processing()

    def hide(self) -> None:
        self._impl.hide()

    def set_preview_text(self, text: str) -> None:
        self._impl.set_preview_text(text)

    def set_status_text(self, text: str) -> None:
        self._impl.set_status_text(text)

    def run(self) -> None:
        self._impl.run()

    def close(self) -> None:
        self._impl.close()

if sys.platform == "darwin":
    import objc
    from AppKit import (
        NSApp,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
        NSBezierPath,
        NSColor,
        NSFont,
        NSFontWeightMedium,
        NSLineBreakByTruncatingTail,
        NSMutableParagraphStyle,
        NSPasteboard,
        NSScreen,
        NSString,
        NSView,
        NSWindow,
        NSWindowCollectionBehaviorCanJoinAllSpaces,
        NSWindowCollectionBehaviorFullScreenAuxiliary,
        NSWindowCollectionBehaviorStationary,
        NSWindowStyleMaskBorderless,
    )
    from Foundation import NSObject

    _TEXT_FONT_SIZE = 13.0
    _TEXT_PADDING_X = 24.0

    def _fit_text_ns(text: str, max_w: float, font: NSFont) -> str:
        text = text.strip()
        if not text:
            return ""
        attrs = {objc.lookUpClass("NSAttributedString").Key("Font"): font}
        ns = NSString.stringWithString_(text)
        if ns.sizeWithAttributes_(attrs).width <= max_w:
            return text
        words = text.split()
        if not words:
            return ""
        for i in range(1, len(words)):
            cand = "… " + " ".join(words[i:])
            if NSString.stringWithString_(cand).sizeWithAttributes_(attrs).width <= max_w:
                return cand
        last_word = words[-1]
        for i in range(len(last_word) - 1, 0, -1):
            cand = "… " + last_word[-i:]
            if NSString.stringWithString_(cand).sizeWithAttributes_(attrs).width <= max_w:
                return cand
        return "…"

    class _NonActivatingWindow(NSWindow):
        def canBecomeKeyWindow(self) -> bool:
            return False
        def canBecomeMainWindow(self) -> bool:
            return False
        def acceptFirstResponder(self) -> bool:
            return False

    class _HUDView(NSView):
        def initWithFrame_(self, frame):
            self = objc.super(_HUDView, self).initWithFrame_(frame)
            if self is None:
                return None
            self._state = "idle"
            self._rms: List[float] = [0.0] * 5
            self._pulse_t = 0.0
            self._raw_preview_text = ""
            self._raw_status_text = ""
            self._fitted_preview_text = ""
            self._fitted_status_text = ""
            self._text_dirty = False
            self._text_w = 0.0
            return self

        def isFlipped(self) -> bool:
            return True

        def setState_(self, state):
            if self._state != state:
                self._state = state
                self._text_dirty = True
                self.setNeedsDisplay_(True)

        def updateRms_(self, rms):
            self._rms = list(rms)

        def tickPulse_(self, dt):
            self._pulse_t += float(dt)

        def setRawPreviewText_(self, text):
            if self._raw_preview_text != text:
                self._raw_preview_text = text
                self._text_dirty = True

        def setRawStatusText_(self, text):
            if self._raw_status_text != text:
                self._raw_status_text = text
                self._text_dirty = True

        def setTextWidth_(self, w):
            self._text_w = float(w)

        def drawRect_(self, dirtyRect):
            bounds = self.bounds()
            w = bounds.size.width
            h = bounds.size.height

            if self._text_dirty or abs(self._text_w - w) > 1.0:
                self._refit_text(w)
                self._text_dirty = False

            radius = 24.0
            path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                ((0.0, 0.0), (w, h)), radius, radius
            )
            NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.05, 0.07, 0.12, 0.90
            ).set()
            path.fill()
            NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.12).set()
            path.setLineWidth_(1.0)
            path.stroke()

            if h >= 70.0:
                self._drawExpanded(w, h)
            else:
                self._drawCollapsed(w, h)

        @objc.python_method
        def _refit_text(self, w: float):
            self._text_w = w
            font = NSFont.systemFontOfSize_weight_(_TEXT_FONT_SIZE, NSFontWeightMedium)
            max_w = max(0.0, w - 2 * _TEXT_PADDING_X)
            self._fitted_preview_text = _fit_text_ns(self._raw_preview_text, max_w, font)
            self._fitted_status_text = _fit_text_ns(self._raw_status_text, max_w, font)

        @objc.python_method
        def _drawCollapsed(self, w: float, h: float) -> None:
            if self._state == "recording":
                self._drawBars(w, h)
            elif self._state == "processing":
                self._drawBreathing(w, h)

        @objc.python_method
        def _drawExpanded(self, w: float, h: float) -> None:
            top_h = h / 2.0
            if self._state == "recording":
                self._drawInkWaveform(w, top_h)
            elif self._state == "processing":
                self._drawBreathing(w, top_h)

            div_path = NSBezierPath.bezierPath()
            div_path.moveToPoint_((24.0, top_h))
            div_path.lineToPoint_((w - 24.0, top_h))
            NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.08).set()
            div_path.setLineWidth_(1.0)
            div_path.stroke()

            is_recording = (self._state == "recording")
            text = self._fitted_preview_text if is_recording else self._fitted_status_text
            if text:
                color = (
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(0.7, 0.75, 0.82, 0.95)
                    if is_recording
                    else NSColor.colorWithCalibratedRed_green_blue_alpha_(0.9, 0.92, 0.96, 0.95)
                )
                font = NSFont.systemFontOfSize_weight_(_TEXT_FONT_SIZE, NSFontWeightMedium)
                attrs = {
                    objc.lookUpClass("NSAttributedString").Key("Font"): font,
                    objc.lookUpClass("NSAttributedString").Key("ForegroundColor"): color,
                }
                ns_text = NSString.stringWithString_(text)
                text_size = ns_text.sizeWithAttributes_(attrs)
                text_y = top_h + (top_h - text_size.height) / 2.0
                ns_text.drawAtPoint_withAttributes_((_TEXT_PADDING_X, text_y), attrs)

        @objc.python_method
        def _drawBars(self, w: float, h: float) -> None:
            n = len(self._rms)
            gap = 5.0
            bar_w = 3.0
            total_w = n * bar_w + (n - 1) * gap
            x0 = (w - total_w) / 2.0
            mid_y = h / 2.0
            max_h = h * 0.55

            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.38, 0.40, 0.95, 1.0).set()
            for i, lvl in enumerate(self._rms):
                bar_h = max(3.0, min(max_h, lvl * max_h * 2.2))
                x = x0 + i * (bar_w + gap)
                rect = ((x, mid_y - bar_h / 2.0), (bar_w, bar_h))
                path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, bar_w / 2.0, bar_w / 2.0)
                path.fill()

        @objc.python_method
        def _drawInkWaveform(self, w: float, top_h: float) -> None:
            mid_y = top_h / 2.0
            max_rms = max(self._rms) if self._rms else 0.0
            x_start = 36.0
            x_end = w - 36.0
            span_w = x_end - x_start
            num_pts = 24

            pts = []
            for i in range(num_pts + 1):
                t = i / float(num_pts)
                x = x_start + t * span_w
                env = math.sin(t * math.pi)
                h1 = math.sin(self._pulse_t * 3.6 + t * 4.0 * math.pi) * (2.5 + 14.0 * max_rms)
                h2 = math.cos(self._pulse_t * 2.2 + t * 2.5 * math.pi) * (1.5 + 7.0 * max_rms)
                y = mid_y + env * (h1 + h2)
                pts.append((x, y))

            glow_path = NSBezierPath.bezierPath()
            glow_path.moveToPoint_(pts[0])
            for pt in pts[1:]:
                glow_path.lineToPoint_(pt)
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.20, 0.22, 0.60, 0.40).set()
            glow_path.setLineWidth_(4.0)
            glow_path.setLineCapStyle_(1)
            glow_path.stroke()

            ink_path = NSBezierPath.bezierPath()
            ink_path.moveToPoint_(pts[0])
            for pt in pts[1:]:
                ink_path.lineToPoint_(pt)
            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.38, 0.40, 0.95, 1.0).set()
            ink_path.setLineWidth_(2.0)
            ink_path.setLineCapStyle_(1)
            ink_path.stroke()

        @objc.python_method
        def _drawBreathing(self, w: float, h: float) -> None:
            n = 3
            d = 6.0
            gap = 7.0
            total_w = n * d + (n - 1) * gap
            x0 = (w - total_w) / 2.0
            mid_y = h / 2.0

            NSColor.colorWithCalibratedRed_green_blue_alpha_(0.38, 0.40, 0.95, 0.9).set()
            for i in range(n):
                phase = self._pulse_t * 2.8 - i * 0.7
                s = 0.5 + 0.5 * math.sin(phase)
                r = d / 2.0 + s * 2.0
                rect = ((x0 + i * (d + gap) + d / 2.0 - r, mid_y - r), (r * 2.0, r * 2.0))
                NSBezierPath.bezierPathWithOvalInRect_(rect).fill()

    class _Animator(NSObject):
        def initWithHud_(self, hud):
            self = objc.super(_Animator, self).init()
            if self is None:
                return None
            self._hud = hud
            return self

        def fire_(self, timer):
            self._hud._tick_animation()

    class _MacOSHUD:
        def __init__(
            self,
            rms_provider: Optional[Callable[[int], List[float]]],
            w_collapsed: int,
            h_collapsed: int,
            w_expanded: int,
            h_expanded: int,
            bottom_margin: int,
            fade_seconds: float,
            size_seconds: float,
        ) -> None:
            self._rms_provider = rms_provider
            self._w_collapsed = w_collapsed
            self._h_collapsed = h_collapsed
            self._w_expanded = w_expanded
            self._h_expanded = h_expanded
            self._bottom_margin = bottom_margin
            self._fade_seconds = fade_seconds
            self._size_seconds = size_seconds

            self._state = "idle"
            self._target_alpha = 0.0
            self._current_alpha = 0.0
            self._target_w = w_collapsed
            self._target_h = h_collapsed
            self._current_w = float(w_collapsed)
            self._current_h = float(h_collapsed)
            self._current_x = 0.0
            self._target_x = 0.0
            self._size_anim_t = 0.0
            self._size_anim_dur = 0.0
            self._size_anim_w0 = float(w_collapsed)
            self._size_anim_h0 = float(h_collapsed)
            self._size_anim_x0 = 0.0

            self._window: Optional[_NonActivatingWindow] = None
            self._view: Optional[_HUDView] = None
            self._app: Optional[NSApplication] = None
            self._timer = None
            self._animator = None
            self._shown = False
            self._screen_origin_x: float = 0.0
            self._screen_origin_y: float = 0.0
            self._screen_w: float = 1920.0
            self._screen_h: float = 1080.0
            self._screen_dirty = True
            self._size_dirty = False
            self._last_tick = time.monotonic()
            self._stop = threading.Event()

            self._setup_window()

        def _setup_window(self) -> None:
            self._app = NSApplication.sharedApplication()
            self._app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
            self._update_screen()

            x = self._screen_origin_x + (self._screen_w - self._w_collapsed) / 2.0
            y = self._screen_origin_y + float(self._bottom_margin)
            rect = ((x, y), (self._w_collapsed, self._h_collapsed))
            self._current_x = x
            self._target_x = x

            win = _NonActivatingWindow.alloc().initWithContentRect_styleMask_backing_defer_(
                rect, NSWindowStyleMaskBorderless, 2, False
            )
            win.setOpaque_(False)
            win.setBackgroundColor_(NSColor.clearColor())
            win.setHasShadow_(True)
            win.setLevel_(101)
            win.setIgnoresMouseEvents_(True)
            win.setCollectionBehavior_(
                NSWindowCollectionBehaviorCanJoinAllSpaces
                | NSWindowCollectionBehaviorStationary
                | NSWindowCollectionBehaviorFullScreenAuxiliary
            )
            win.setAlphaValue_(0.0)

            view = _HUDView.alloc().initWithFrame_(((0.0, 0.0), (self._w_collapsed, self._h_collapsed)))
            win.setContentView_(view)

            self._window = win
            self._view = view

        def _update_screen(self) -> None:
            screen = NSScreen.mainScreen()
            if screen is not None:
                vis = screen.visibleFrame()
                self._screen_origin_x = vis.origin.x
                self._screen_origin_y = vis.origin.y
                self._screen_w = vis.size.width
                self._screen_h = vis.size.height

        def show_recording(self, preview_active: bool) -> None:
            self._state = "recording"
            self._target_alpha = 0.92
            self._screen_dirty = True
            target_w = self._w_expanded if preview_active else self._w_collapsed
            target_h = self._h_expanded if preview_active else self._h_collapsed
            self._target_w = target_w
            self._target_h = target_h
            self._size_dirty = True
            if self._view is not None:
                self._view.setRawPreviewText_("")
                self._view.setRawStatusText_("")

        def show_processing(self) -> None:
            self._state = "processing"
            self._target_alpha = 0.92
            self._screen_dirty = True
            self._target_w = self._w_expanded
            self._target_h = self._h_expanded
            self._size_dirty = True
            if self._view is not None:
                self._view.setRawPreviewText_("")
                self._view.setRawStatusText_("Transcribing with Whisper...")

        def set_preview_text(self, text: str) -> None:
            if self._view is not None:
                self._view.setRawPreviewText_(text)

        def set_status_text(self, text: str) -> None:
            if self._view is not None:
                self._view.setRawStatusText_(text)

        def hide(self) -> None:
            self._state = "idle"
            self._target_alpha = 0.0
            self._target_w = self._w_collapsed
            self._target_h = self._h_collapsed
            self._size_dirty = True
            if self._view is not None:
                self._view.setRawPreviewText_("")
                self._view.setRawStatusText_("")

        def close(self) -> None:
            self._stop.set()

        def _set_size_target(self, w: int, h: int) -> None:
            if w == self._target_w and h == self._target_h:
                return
            new_x = self._screen_origin_x + (self._screen_w - w) / 2.0
            self._size_anim_w0 = self._current_w
            self._size_anim_h0 = self._current_h
            self._size_anim_x0 = self._current_x
            self._target_w = w
            self._target_h = h
            self._target_x = new_x
            self._size_anim_t = 0.0
            self._size_anim_dur = self._size_seconds

        def _tick_animation(self) -> None:
            now = time.monotonic()
            dt = max(0.0, now - self._last_tick)
            self._last_tick = now

            if self._window is None or self._view is None:
                return

            self._view.setState_(self._state)

            if self._screen_dirty:
                self._update_screen()
                target_w = self._target_w
                target_h = self._target_h
                new_x = self._screen_origin_x + (self._screen_w - target_w) / 2.0
                if self._current_alpha <= 0.01:
                    self._current_x = new_x
                    self._target_x = new_x
                    self._current_w = float(target_w)
                    self._current_h = float(target_h)
                    self._size_anim_dur = 0.0
                    self._apply_geometry()
                else:
                    self._set_size_target(target_w, target_h)
                self._screen_dirty = False
            elif self._size_dirty:
                self._set_size_target(self._target_w, self._target_h)
                self._size_dirty = False

            if not self._shown and self._target_alpha > 0.0:
                self._window.orderFrontRegardless()
                self._shown = True

            if abs(self._target_alpha - self._current_alpha) > 0.001:
                step = dt / max(self._fade_seconds, 1e-3)
                if self._target_alpha > self._current_alpha:
                    self._current_alpha = min(self._target_alpha, self._current_alpha + step)
                else:
                    self._current_alpha = max(self._target_alpha, self._current_alpha - step)
                self._window.setAlphaValue_(self._current_alpha)

            if self._current_alpha <= 0.001 and self._target_alpha == 0.0:
                if self._shown:
                    self._window.orderOut_(None)
                    self._shown = False

            size_changed = (
                abs(self._target_w - self._current_w) > 0.5
                or abs(self._target_h - self._current_h) > 0.5
            )
            if size_changed and self._size_anim_dur > 0.0:
                self._size_anim_t += dt
                progress = min(1.0, self._size_anim_t / self._size_anim_dur)
                eased = 1.0 - (1.0 - progress) ** 3
                self._current_w = self._size_anim_w0 + (self._target_w - self._size_anim_w0) * eased
                self._current_h = self._size_anim_h0 + (self._target_h - self._size_anim_h0) * eased
                self._current_x = self._size_anim_x0 + (self._target_x - self._size_anim_x0) * eased
                self._apply_geometry()

            if self._state == "recording":
                if self._rms_provider is not None:
                    self._view.updateRms_(self._rms_provider(5))
                else:
                    self._view.updateRms_([0.0] * 5)
                self._view.tickPulse_(dt)
            elif self._state == "processing":
                self._view.tickPulse_(dt)

            if self._state != "idle" or self._current_alpha > 0.01:
                self._view.setNeedsDisplay_(True)

        def _apply_geometry(self) -> None:
            if self._window is None:
                return
            y = self._screen_origin_y + float(self._bottom_margin)
            rect = ((self._current_x, y), (self._current_w, self._current_h))
            self._window.setFrame_display_(rect, True)
            if self._view is not None:
                self._view.setTextWidth_(self._current_w)

        def run(self) -> None:
            assert self._app is not None
            from AppKit import NSTimer

            self._animator = _Animator.alloc().initWithHud_(self)
            self._timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.016, self._animator, "fire:", None, True
            )
            try:
                self._app.run()
            except KeyboardInterrupt:
                pass

else:
    import tkinter as tk
    from tkinter import font as tkfont
    from ._platform import IS_LINUX, IS_WINDOWS

    _IS_WINDOWS = IS_WINDOWS
    _WITHDRAW_WHEN_HIDDEN = IS_LINUX

    if _IS_WINDOWS:
        import ctypes
        from ctypes import wintypes

        _user32 = ctypes.windll.user32
        GWL_EXSTYLE = -20
        WS_EX_NOACTIVATE = 0x08000000
        WS_EX_TOOLWINDOW = 0x00000080

        if ctypes.sizeof(ctypes.c_void_p) == 8:
            _SetWindowLongPtrW = _user32.SetWindowLongPtrW
            _SetWindowLongPtrW.restype = wintypes.LONG_PTR
            _SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG_PTR]
            _GetWindowLongPtrW = _user32.GetWindowLongPtrW
            _GetWindowLongPtrW.restype = wintypes.LONG_PTR
            _GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
        else:
            _SetWindowLongPtrW = _user32.SetWindowLongW
            _SetWindowLongPtrW.restype = wintypes.LONG
            _SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
            _GetWindowLongPtrW = _user32.GetWindowLongW
            _GetWindowLongPtrW.restype = wintypes.LONG
            _GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]

    _BG = "#0B0F19"
    _ACCENT = "#6366F1"
    _GLOW_ACCENT = "#312E81"
    _TEXT_COLOR = "#CBD5E1"
    _STATUS_COLOR = "#F8FAFC"
    _DIVIDER_COLOR = "#1E293B"
    _TEXT_FONT_FAMILY = "Segoe UI" if _IS_WINDOWS else "DejaVu Sans"
    _TEXT_FONT_SIZE = 12
    _TEXT_PADDING_X = 22

    def _get_active_monitor_work_area():
        if not _IS_WINDOWS:
            return None
        try:
            hwnd = _user32.GetForegroundWindow()
            hmon = 0
            if hwnd:
                hmon = _user32.MonitorFromWindow(hwnd, 2)
            if not hmon:
                pt = wintypes.POINT()
                _user32.GetCursorPos(ctypes.byref(pt))
                hmon = _user32.MonitorFromPoint(pt, 2)
            if hmon:
                class MONITORINFO(ctypes.Structure):
                    _fields_ = [
                        ("cbSize", wintypes.DWORD),
                        ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT),
                        ("dwFlags", wintypes.DWORD),
                    ]
                mi = MONITORINFO()
                mi.cbSize = ctypes.sizeof(MONITORINFO)
                if _user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                    return (
                        mi.rcWork.left,
                        mi.rcWork.top,
                        mi.rcWork.right - mi.rcWork.left,
                        mi.rcWork.bottom - mi.rcWork.top,
                    )
        except Exception:
            pass
        return None

    def _fit_text_tk(text: str, max_w: int, font: "tkfont.Font") -> str:
        text = text.strip()
        if not text:
            return ""
        if font.measure(text) <= max_w:
            return text
        words = text.split()
        if not words:
            return ""
        for i in range(1, len(words)):
            cand = "… " + " ".join(words[i:])
            if font.measure(cand) <= max_w:
                return cand
        last_word = words[-1]
        for i in range(len(last_word) - 1, 0, -1):
            cand = "… " + last_word[-i:]
            if font.measure(cand) <= max_w:
                return cand
        return "…"

    class _TkHUD:
        def __init__(
            self,
            rms_provider: Optional[Callable[[int], List[float]]],
            w_collapsed: int,
            h_collapsed: int,
            w_expanded: int,
            h_expanded: int,
            bottom_margin: int,
            fade_seconds: float,
            size_seconds: float,
        ) -> None:
            self._rms_provider = rms_provider
            self._w_collapsed = w_collapsed
            self._h_collapsed = h_collapsed
            self._w_expanded = w_expanded
            self._h_expanded = h_expanded
            self._bottom_margin = bottom_margin
            self._fade_seconds = fade_seconds
            self._size_seconds = size_seconds
            self._state = "idle"
            self._target_alpha = 0.0
            self._current_alpha = 0.0
            self._shown = False
            self._events: "queue.Queue[tuple]" = queue.Queue()

            self._screen_origin_x: float = 0.0
            self._screen_origin_y: float = 0.0
            self._screen_w: float = 1920.0
            self._screen_h: float = 1080.0

            self._target_w = w_collapsed
            self._target_h = h_collapsed
            self._current_w = float(w_collapsed)
            self._current_h = float(h_collapsed)
            self._current_x = 0.0
            self._target_x = 0.0
            self._size_anim_t = 0.0
            self._size_anim_dur = 0.0
            self._size_anim_w0 = float(w_collapsed)
            self._size_anim_h0 = float(h_collapsed)
            self._size_anim_x0 = 0.0
            self._pulse_t = 0.0

            self._raw_preview = ""
            self._raw_status = ""
            self._fitted_preview = ""
            self._fitted_status = ""
            self._text_dirty = False

            self._top = None
            self._withdrawn = False

            self._stop = threading.Event()
            self._thread = threading.Thread(target=self._run, daemon=True, name="voice-hud")
            self._thread.start()

        def show_recording(self, preview_active: bool) -> None:
            self._events.put(("recording", preview_active))

        def show_processing(self) -> None:
            self._events.put(("processing", True))

        def set_preview_text(self, text: str) -> None:
            self._events.put(("preview_text", text))

        def set_status_text(self, text: str) -> None:
            self._events.put(("status_text", text))

        def hide(self) -> None:
            self._events.put(("hide", None))

        def close(self) -> None:
            self._stop.set()
            self._events.put(("stop", None))
            if threading.current_thread() is not self._thread:
                self._thread.join(timeout=1.0)

        def run(self) -> None:
            while self._thread.is_alive():
                self._thread.join(timeout=0.2)

        def _update_screen(self) -> None:
            work = _get_active_monitor_work_area()
            if work:
                self._screen_origin_x, self._screen_origin_y, self._screen_w, self._screen_h = work
            elif hasattr(self, "_top") and self._top:
                self._screen_origin_x = 0.0
                self._screen_origin_y = 0.0
                self._screen_w = float(self._top.winfo_screenwidth())
                self._screen_h = float(self._top.winfo_screenheight())

        def _run(self) -> None:
            try:
                root = tk.Tk()
            except Exception:
                log.warning("HUD overlay unavailable (Tk display error).")
                self._stop.wait()
                return
            root.withdraw()

            top = tk.Toplevel(root)
            top.overrideredirect(True)
            self._top = top

            self._update_screen()
            x = self._screen_origin_x + (self._screen_w - self._w_collapsed) / 2.0
            y = self._screen_origin_y + self._screen_h - self._h_collapsed - self._bottom_margin
            top.geometry(f"{self._w_collapsed}x{self._h_collapsed}+{int(x)}+{int(y)}")
            try:
                top.attributes("-topmost", True)
            except tk.TclError:
                pass
            try:
                top.attributes("-alpha", 0.0)
            except tk.TclError:
                pass
            top.configure(bg=_BG)
            self._current_x = float(x)
            self._target_x = float(x)

            top.update_idletasks()
            if _IS_WINDOWS:
                try:
                    hwnd = (
                        int(top.wm_frame(), 16)
                        or _user32.GetParent(top.winfo_id())
                        or top.winfo_id()
                    )
                    style = _GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
                    style |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
                    _SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
                except Exception:
                    pass
            if _WITHDRAW_WHEN_HIDDEN:
                top.withdraw()
                self._withdrawn = True

            self._text_font = tkfont.Font(family=_TEXT_FONT_FAMILY, size=_TEXT_FONT_SIZE, weight="bold")
            canvas = tk.Canvas(
                top,
                width=self._w_collapsed,
                height=self._h_collapsed,
                bg=_BG,
                highlightthickness=0,
                bd=0,
            )
            canvas.pack()

            self._canvas = canvas
            self._root = root
            self._last_tick = time.monotonic()
            self._tick()
            root.mainloop()

        def _tick(self) -> None:
            now = time.monotonic()
            dt = max(0.0, now - self._last_tick)
            self._last_tick = now
            self._pulse_t += dt

            try:
                while True:
                    kind, payload = self._events.get_nowait()
                    if kind == "recording":
                        self._state = "recording"
                        self._target_alpha = 0.94
                        self._ensure_mapped()
                        self._update_screen()
                        preview_active = bool(payload)
                        target_w = self._w_expanded if preview_active else self._w_collapsed
                        target_h = self._h_expanded if preview_active else self._h_collapsed

                        new_x = self._screen_origin_x + (self._screen_w - target_w) / 2.0
                        if self._current_alpha <= 0.01:
                            self._current_x = new_x
                            self._target_x = new_x
                            self._current_w = float(target_w)
                            self._current_h = float(target_h)
                            self._target_w = target_w
                            self._target_h = target_h
                            self._size_anim_dur = 0.0
                            self._apply_geometry()
                        else:
                            self._set_size_target(target_w, target_h)

                        self._raw_preview = ""
                        self._raw_status = ""
                        self._text_dirty = True
                    elif kind == "processing":
                        self._state = "processing"
                        self._target_alpha = 0.94
                        self._ensure_mapped()
                        self._set_size_target(self._w_expanded, self._h_expanded)
                        self._raw_preview = ""
                        self._raw_status = "Transcribing with Whisper..."
                        self._text_dirty = True
                    elif kind == "preview_text":
                        new_text = str(payload)
                        if new_text != self._raw_preview:
                            self._raw_preview = new_text
                            self._text_dirty = True
                    elif kind == "status_text":
                        new_text = str(payload)
                        if new_text != self._raw_status:
                            self._raw_status = new_text
                            self._text_dirty = True
                    elif kind == "hide":
                        self._state = "idle"
                        self._target_alpha = 0.0
                        self._set_size_target(self._w_collapsed, self._h_collapsed)
                        self._raw_preview = ""
                        self._raw_status = ""
                        self._text_dirty = True
                    elif kind == "stop":
                        self._root.quit()
                        return
            except queue.Empty:
                pass

            if abs(self._target_alpha - self._current_alpha) > 0.005:
                step = dt / max(self._fade_seconds, 1e-3)
                if self._target_alpha > self._current_alpha:
                    self._current_alpha = min(self._target_alpha, self._current_alpha + step)
                else:
                    self._current_alpha = max(self._target_alpha, self._current_alpha - step)
                try:
                    self._top.attributes("-alpha", self._current_alpha)
                except tk.TclError:
                    if self._top is None or not self._top.winfo_exists():
                        return

            if (
                self._state == "idle"
                and self._target_alpha <= 0.0
                and self._current_alpha <= 0.01
            ):
                self._maybe_withdraw()

            if (
                abs(self._target_w - self._current_w) > 0.5
                or abs(self._target_h - self._current_h) > 0.5
            ) and self._size_anim_dur > 0.0:
                self._size_anim_t += dt
                progress = min(1.0, self._size_anim_t / self._size_anim_dur)
                eased = 1.0 - (1.0 - progress) ** 3
                self._current_w = self._size_anim_w0 + (self._target_w - self._size_anim_w0) * eased
                self._current_h = self._size_anim_h0 + (self._target_h - self._size_anim_h0) * eased
                self._current_x = self._size_anim_x0 + (self._target_x - self._size_anim_x0) * eased
                self._apply_geometry()

            if self._text_dirty:
                self._refit_text()
                self._text_dirty = False

            if self._state != "idle" or self._current_alpha > 0.01:
                self._redraw()
            self._root.after(16, self._tick)

        def _ensure_mapped(self) -> None:
            if not self._withdrawn or self._top is None:
                return
            try:
                self._top.deiconify()
                self._top.lift()
                self._top.attributes("-topmost", True)
            except tk.TclError:
                return
            self._withdrawn = False

        def _maybe_withdraw(self) -> None:
            if not _WITHDRAW_WHEN_HIDDEN or self._withdrawn or self._top is None:
                return
            try:
                self._top.withdraw()
            except tk.TclError:
                return
            self._withdrawn = True

        def _refit_text(self) -> None:
            text_w = max(0, int(self._current_w) - 2 * _TEXT_PADDING_X)
            self._fitted_preview = _fit_text_tk(self._raw_preview, text_w, self._text_font)
            self._fitted_status = _fit_text_tk(self._raw_status, text_w, self._text_font)

        def _set_size_target(self, w: int, h: int) -> None:
            if w == self._target_w and h == self._target_h:
                return
            new_x = self._screen_origin_x + (self._screen_w - w) / 2.0
            self._size_anim_w0 = self._current_w
            self._size_anim_h0 = self._current_h
            self._size_anim_x0 = self._current_x
            self._target_w = w
            self._target_h = h
            self._target_x = new_x
            self._size_anim_t = 0.0
            self._size_anim_dur = self._size_seconds

        def _apply_geometry(self) -> None:
            if self._top is None:
                return
            y = self._screen_origin_y + self._screen_h - self._current_h - self._bottom_margin
            self._top.geometry(
                f"{int(self._current_w)}x{int(self._current_h)}"
                f"+{int(self._current_x)}+{int(y)}"
            )
            self._canvas.configure(width=int(self._current_w), height=int(self._current_h))

        def _redraw(self) -> None:
            canvas = self._canvas
            w = self._current_w
            h = self._current_h
            canvas.delete("all")

            r = 24.0
            canvas.create_oval(0, 0, r * 2, h, fill=_BG, outline="")
            canvas.create_oval(w - r * 2, 0, w, h, fill=_BG, outline="")
            canvas.create_rectangle(r, 0, w - r, h, fill=_BG, outline="")

            if h >= 70.0:
                self._draw_expanded(w, h)
            else:
                self._draw_collapsed(w, h)

        def _draw_collapsed(self, w: float, h: float) -> None:
            if self._state == "recording":
                rms = self._rms_provider(5) if self._rms_provider else [0.0] * 5
                self._draw_bars(w, h, rms)
            elif self._state == "processing":
                self._draw_breathing(w, h)

        def _draw_expanded(self, w: float, h: float) -> None:
            top_h = h / 2.0
            if self._state == "recording":
                rms = self._rms_provider(5) if self._rms_provider else [0.0] * 5
                self._draw_ink_waveform(w, top_h, rms)
            elif self._state == "processing":
                self._draw_breathing(w, top_h)

            canvas = self._canvas
            canvas.create_rectangle(
                24, top_h - 0.5, w - 24, top_h + 0.5,
                fill=_DIVIDER_COLOR, outline="",
            )

            is_recording = (self._state == "recording")
            text = self._fitted_preview if is_recording else self._fitted_status
            if text:
                color = _TEXT_COLOR if is_recording else _STATUS_COLOR
                text_y = top_h + (top_h - 16.0) / 2.0
                canvas.create_text(
                    _TEXT_PADDING_X, text_y,
                    text=text, font=self._text_font,
                    fill=color, anchor="nw",
                )

        def _draw_ink_waveform(self, w: float, top_h: float, rms: List[float]) -> None:
            mid_y = top_h / 2.0
            max_rms = max(rms) if rms else 0.0
            x_start = 36.0
            x_end = w - 36.0
            span_w = x_end - x_start
            num_pts = 16

            flat_points = []
            for i in range(num_pts + 1):
                t = i / float(num_pts)
                x = x_start + t * span_w
                env = math.sin(t * math.pi)
                h1 = math.sin(self._pulse_t * 3.6 + t * 4.0 * math.pi) * (2.5 + 14.0 * max_rms)
                h2 = math.cos(self._pulse_t * 2.2 + t * 2.5 * math.pi) * (1.5 + 7.0 * max_rms)
                y = mid_y + env * (h1 + h2)
                flat_points.extend([x, y])

            self._canvas.create_line(
                flat_points, smooth=True, fill=_GLOW_ACCENT, width=4, capstyle=tk.ROUND
            )
            self._canvas.create_line(
                flat_points, smooth=True, fill=_ACCENT, width=2, capstyle=tk.ROUND
            )

        def _draw_bars(self, w: float, h: float, rms: List[float]) -> None:
            n = 5
            gap = 5.0
            bar_w = 3.0
            total = n * bar_w + (n - 1) * gap
            x0 = (w - total) / 2.0
            mid = h / 2.0
            max_h = h * 0.55
            for i, lvl in enumerate(rms):
                lh = max(3.0, min(max_h, lvl * max_h * 2.2))
                x = x0 + i * (bar_w + gap)
                self._canvas.create_oval(
                    x, mid - lh / 2.0,
                    x + bar_w, mid + lh / 2.0,
                    fill=_ACCENT, outline="",
                )

        def _draw_breathing(self, w: float, h: float) -> None:
            n = 3
            d = 6.0
            gap = 7.0
            total = n * d + (n - 1) * gap
            x0 = (w - total) / 2.0
            mid_y = h / 2.0
            for i in range(n):
                phase = self._pulse_t * 2.8 - i * 0.7
                s = 0.5 + 0.5 * math.sin(phase)
                r = d / 2.0 + s * 2.0
                self._canvas.create_oval(
                    x0 + i * (d + gap) + d / 2.0 - r,
                    mid_y - r,
                    x0 + i * (d + gap) + d / 2.0 + r,
                    mid_y + r,
                    fill=_ACCENT, outline="",
                )

    _WindowsHUD = _TkHUD
