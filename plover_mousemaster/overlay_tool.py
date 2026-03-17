"""
Overlay Tool - A plover.gui_qt.tool.Tool subclass that manages the transparent overlay.
Runs on Plover's main GUI thread. Plover 5.1.0 uses PySide6.
"""
from plover.engine import StenoEngine
from plover.gui_qt.tool import Tool

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QRect, Slot, QTimer, QPoint
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QCursor

from .mouse_control import MouseControl

import os
import threading
import ctypes

_DEBUG_LOG = os.path.join(os.path.expanduser("~"), "plover_mouse_debug.log")

def _log(msg):
    try:
        with open(_DEBUG_LOG, "a") as f:
            tid = threading.current_thread().name
            f.write(f"[{tid}] {msg}\n")
    except:
        pass


class OverlayTool(Tool):
    TITLE = "Mouse Overlay"
    ICON = ""
    ROLE = "mouse_overlay"

    def __init__(self, engine: StenoEngine) -> None:
        super().__init__(engine)
        _log(f"OverlayTool.__init__ on thread={threading.current_thread().name}")
        self._engine = engine

        self.grid_visible = False
        self.grid_rect = QRect()       # absolute screen coords
        self.all_hints = []            # full list of (x, y, label) - absolute coords
        self.visible_hints = []        # filtered list currently displayed
        self._hint_active = False
        self._hint_prefix = ""
        self._hint_manager = None      # set externally after scan

        # Make it frameless, always on top, translucent, click-through
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Default to primary screen
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        else:
            self.setGeometry(0, 0, 1920, 1080)

        # 5-second inactivity timeout for hint mode
        self._hint_timer = QTimer(self)
        self._hint_timer.setSingleShot(True)
        self._hint_timer.setInterval(5000)
        self._hint_timer.timeout.connect(self._on_hint_timeout)

        # 10-second inactivity timeout for grid mode
        self._grid_timer = QTimer(self)
        self._grid_timer.setSingleShot(True)
        self._grid_timer.setInterval(10000)
        self._grid_timer.timeout.connect(self._on_grid_timeout)

        # Z-order enforcement timer - keep overlay on top
        self._topmost_timer = QTimer(self)
        self._topmost_timer.setInterval(200)
        self._topmost_timer.timeout.connect(self._enforce_topmost)

        # Hook into Plover's translated output for natural letter capture
        engine.signal_connect("translated", self._on_translated)

        # Register globally so command plugins can find us
        _register_overlay(self)
        _log("OverlayTool registered globally")

    def _enforce_topmost(self):
        """Periodically force the overlay to stay on top of all windows."""
        if self.isVisible():
            try:
                hwnd = int(self.winId())
                HWND_TOPMOST = -1
                SWP_NOMOVE = 0x0002
                SWP_NOSIZE = 0x0001
                SWP_NOACTIVATE = 0x0010
                ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
                )
            except:
                pass

    def _to_local(self, abs_x, abs_y):
        """Convert absolute screen coordinates to widget-local coordinates."""
        geo = self.geometry()
        return abs_x - geo.x(), abs_y - geo.y()

    def _send_backspace(self):
        """Send a backspace keystroke to undo a letter Plover just output."""
        VK_BACK = 0x08
        KEYEVENTF_KEYUP = 0x0002
        ctypes.windll.user32.keybd_event(VK_BACK, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_BACK, 0, KEYEVENTF_KEYUP, 0)

    def _on_translated(self, old, new):
        """Called when Plover translates a stroke to text output."""
        if not self._hint_active:
            return
        if not new:
            return

        for action in new:
            if hasattr(action, 'text') and action.text:
                text = action.text.strip()
                if not text:
                    continue
                # Single letters for hint input
                if len(text) == 1 and text.isalpha():
                    letter = text.lower()
                    _log(f"Hint capture: letter='{letter}', prefix='{self._hint_prefix}'")
                    # Undo the letter that Plover already typed
                    self._send_backspace()
                    self._process_hint_letter(letter)

    def _process_hint_letter(self, letter):
        """Process a typed letter during hint mode."""
        self._hint_prefix += letter
        _log(f"Hint prefix now: '{self._hint_prefix}'")

        # Restart the timeout
        self._hint_timer.start()

        # Check for exact match
        if self._hint_manager:
            coord = self._hint_manager.get_coordinate(self._hint_prefix)
            if coord:
                # Check if there are OTHER labels that start with this prefix
                # If not, it's an unambiguous match — go ahead and click
                matching = self._hint_manager.get_matching_labels(self._hint_prefix)
                if len(matching) == 1:
                    _log(f"Hint match! prefix='{self._hint_prefix}', coord={coord}")
                    MouseControl.move_to(coord[0], coord[1])
                    MouseControl.click('left')
                    self._close_hints()
                    return
                # If there are multiple matches (e.g. 'a' matches 'a' and 'ab'),
                # this can only happen with mixed-length labels.
                # Since we use uniform length, this shouldn't happen, but handle it:
                if len(matching) == 1 or (coord and len(self._hint_prefix) == len(matching[0])):
                    _log(f"Exact match: '{self._hint_prefix}', coord={coord}")
                    MouseControl.move_to(coord[0], coord[1])
                    MouseControl.click('left')
                    self._close_hints()
                    return

        # Filter visible hints
        self.visible_hints = [
            (x, y, label) for x, y, label in self.all_hints
            if label.startswith(self._hint_prefix)
        ]
        _log(f"Filtered to {len(self.visible_hints)} hints matching '{self._hint_prefix}'")

        if len(self.visible_hints) == 0:
            _log("No matching hints, closing")
            self._close_hints()
            return

        # If exactly one hint remains, auto-select it
        if len(self.visible_hints) == 1:
            x, y, label = self.visible_hints[0]
            _log(f"Single remaining hint: '{label}', clicking")
            MouseControl.move_to(x, y)
            MouseControl.click('left')
            self._close_hints()
            return

        self.update()

    def _on_hint_timeout(self):
        _log("Hint mode timed out")
        self._close_hints()

    def _on_grid_timeout(self):
        _log("Grid mode timed out")
        self.grid_visible = False
        self._grid_timer.stop()
        self._topmost_timer.stop()
        self.update()
        self.hide()

    def _close_hints(self):
        self._hint_active = False
        self._hint_prefix = ""
        self.all_hints = []
        self.visible_hints = []
        self._hint_timer.stop()
        self._topmost_timer.stop()
        if self._hint_manager:
            self._hint_manager.clear()
        self.update()
        self.hide()

    @Slot()
    def move_to_cursor_screen(self):
        """Resize and reposition overlay to cover the monitor the cursor is on."""
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            _log(f"Moving overlay to screen: {geo}")
            self.setGeometry(geo)

    @Slot(QRect)
    def show_grid(self, rect):
        _log(f"show_grid rect={rect}")
        # Move overlay to the screen containing the grid rect center
        center = rect.center()
        screen = QApplication.screenAt(center)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        
        self.grid_rect = rect
        self.grid_visible = True
        self._grid_timer.start()
        self._topmost_timer.start()
        self.show()
        self.raise_()
        self._enforce_topmost()
        self.update()

    @Slot()
    def reset_grid_timer(self):
        """Reset the grid timeout (called each time a grid command is used)."""
        if self.grid_visible:
            self._grid_timer.start()

    @Slot()
    def hide_grid(self):
        self.grid_visible = False
        self._grid_timer.stop()
        self._topmost_timer.stop()
        self.hide()

    @Slot()
    def activate_hints(self):
        _log(f"activate_hints: {len(self.all_hints)} hints")
        self.move_to_cursor_screen()
        self._hint_active = True
        self._hint_prefix = ""
        self.visible_hints = list(self.all_hints)
        self._hint_timer.start()
        self._topmost_timer.start()
        self.show()
        self.raise_()
        self._enforce_topmost()
        self.update()

    @Slot()
    def deactivate_hints(self):
        self._close_hints()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.grid_visible:
            self._draw_grid(painter)

        if self.visible_hints:
            self._draw_hints(painter)

    def _draw_grid(self, painter):
        pen = QPen(QColor(255, 0, 0, 150))
        pen.setWidth(2)
        painter.setPen(pen)

        # Convert absolute grid rect to widget-local coordinates
        geo = self.geometry()
        local_rect = QRect(
            self.grid_rect.x() - geo.x(),
            self.grid_rect.y() - geo.y(),
            self.grid_rect.width(),
            self.grid_rect.height()
        )

        painter.drawLine(local_rect.left(), local_rect.center().y(),
                         local_rect.right(), local_rect.center().y())
        painter.drawLine(local_rect.center().x(), local_rect.top(),
                         local_rect.center().x(), local_rect.bottom())
        painter.drawRect(local_rect)

    def _draw_hints(self, painter):
        font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font)
        geo = self.geometry()

        for x, y, label in self.visible_hints:
            lx = x - geo.x()
            ly = y - geo.y()

            text_rect = painter.fontMetrics().boundingRect(label)
            text_rect.moveCenter(QPoint(lx, ly))
            text_rect.adjust(-5, -5, 5, 5)

            # Background box
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRect(text_rect)

            prefix_len = len(self._hint_prefix)

            if prefix_len > 0 and label.startswith(self._hint_prefix):
                prefix_part = label[:prefix_len]
                remaining = label[prefix_len:]
                
                fm = painter.fontMetrics()
                prefix_width = fm.horizontalAdvance(prefix_part)
                total_width = fm.horizontalAdvance(label)
                
                text_x = text_rect.center().x() - total_width // 2
                text_y = text_rect.center().y() + fm.ascent() // 2
                
                painter.setPen(QColor(255, 255, 0))
                painter.drawText(text_x, text_y, prefix_part)
                
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(text_x + prefix_width, text_y, remaining)
            else:
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(text_rect, Qt.AlignCenter, label)


# ---- Global instance registry ----
_overlay_instance = None

def _register_overlay(tool):
    global _overlay_instance
    _overlay_instance = tool
    _log("_overlay_instance set")

def get_overlay():
    return _overlay_instance
