"""
Overlay Tool - A plover.gui_qt.tool.Tool subclass that manages the transparent overlay.
Runs on Plover's main GUI thread. Plover 5.1.0 uses PySide6.
"""
from plover.engine import StenoEngine
from plover.gui_qt.tool import Tool

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QRect, Slot, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QCursor

from .mouse_control import MouseControl

import os
import threading

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
        self.grid_rect = QRect()
        self.all_hints = []       # Full list of (x, y, label) from scan
        self.visible_hints = []   # Filtered list currently displayed
        self._hint_active = False
        self._hint_prefix = ""
        self._hint_manager = None  # Set externally after scan

        # Make it frameless, always on top, translucent
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

        # Hook into Plover's translated output for natural letter capture
        engine.signal_connect("translated", self._on_translated)

        # Register globally so command plugins can find us
        _register_overlay(self)
        _log("OverlayTool registered globally")

    def _on_translated(self, old, new):
        """Called when Plover translates a stroke to text output."""
        if not self._hint_active:
            return
        if not new:
            return

        # Extract the text that was just output
        for action in new:
            if hasattr(action, 'text') and action.text:
                text = action.text.strip()
                if not text:
                    continue
                    
                # We only care about single lowercase letters
                if len(text) == 1 and text.isalpha():
                    letter = text.lower()
                    _log(f"Hint capture: letter='{letter}', current prefix='{self._hint_prefix}'")
                    self._process_hint_letter(letter)

    def _process_hint_letter(self, letter):
        """Process a typed letter during hint mode."""
        self._hint_prefix += letter
        _log(f"Hint prefix now: '{self._hint_prefix}'")

        # Restart the timeout
        self._hint_timer.start()

        # Check if we have an exact match
        from .hints import HintManager
        if self._hint_manager:
            coord = self._hint_manager.get_coordinate(self._hint_prefix)
            if coord:
                _log(f"Hint match! prefix='{self._hint_prefix}', coord={coord}")
                # Move and click
                MouseControl.move_to(coord[0], coord[1])
                MouseControl.click('left')
                self._close_hints()
                return

        # Filter visible hints to only those starting with current prefix
        self.visible_hints = [
            (x, y, label) for x, y, label in self.all_hints
            if label.startswith(self._hint_prefix)
        ]
        _log(f"Filtered hints to {len(self.visible_hints)} matching prefix '{self._hint_prefix}'")

        if len(self.visible_hints) == 0:
            # No matches, close hints
            _log("No matching hints, closing")
            self._close_hints()
            return

        self.update()

    def _on_hint_timeout(self):
        """Called when hint mode times out after 5 seconds of inactivity."""
        _log("Hint mode timed out")
        self._close_hints()

    def _close_hints(self):
        """Close hint mode and reset state."""
        self._hint_active = False
        self._hint_prefix = ""
        self.all_hints = []
        self.visible_hints = []
        self._hint_timer.stop()
        if self._hint_manager:
            self._hint_manager.clear()
        self.update()
        self.hide()

    @Slot()
    def set_active_screen_from_cursor(self):
        """Resize overlay to cover the monitor that the cursor is currently on."""
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
            _log(f"Overlay moved to screen: {screen.geometry()}")

    @Slot(QRect)
    def show_grid(self, rect):
        _log(f"show_grid called, rect={rect}")
        self.set_active_screen_from_cursor()
        self.grid_rect = rect
        self.grid_visible = True
        self.show()
        self.raise_()
        self.update()

    @Slot()
    def hide_grid(self):
        self.grid_visible = False
        self.hide()

    @Slot()
    def activate_hints(self):
        """Start hint mode — hints should already be set via all_hints."""
        _log(f"activate_hints: {len(self.all_hints)} hints, active={self._hint_active}")
        self.set_active_screen_from_cursor()
        self._hint_active = True
        self._hint_prefix = ""
        self.visible_hints = list(self.all_hints)
        self._hint_timer.start()
        self.show()
        self.raise_()
        self.update()

    @Slot()
    def deactivate_hints(self):
        """Manually close hint mode."""
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

        r = self.grid_rect
        painter.drawLine(r.left(), r.center().y(), r.right(), r.center().y())
        painter.drawLine(r.center().x(), r.top(), r.center().x(), r.bottom())
        painter.drawRect(r)

    def _draw_hints(self, painter):
        font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font)

        # Get the overlay's geometry offset (for multi-monitor coordinate mapping)
        geo = self.geometry()

        for x, y, label in self.visible_hints:
            # Convert absolute screen coords to widget-relative coords
            rel_x = x - geo.x()
            rel_y = y - geo.y()

            text_rect = painter.fontMetrics().boundingRect(label)
            text_rect.moveCenter(QRect(rel_x, rel_y, 1, 1).center())
            text_rect.adjust(-5, -5, 5, 5)

            painter.setBrush(QColor(0, 0, 0, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRect(text_rect)

            # Highlight the already-typed prefix in yellow, rest in white
            prefix_len = len(self._hint_prefix)
            
            # Draw the full label first in white
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(text_rect, Qt.AlignCenter, label)
            
            # If we have a prefix, overdraw it in yellow
            if prefix_len > 0 and label.startswith(self._hint_prefix):
                prefix_text = label[:prefix_len]
                # Calculate the prefix portion position
                prefix_rect = painter.fontMetrics().boundingRect(prefix_text)
                prefix_rect.moveTopLeft(text_rect.topLeft())
                prefix_rect.adjust(5, 5, 5, 0)  # manual alignment adjustment
                painter.setPen(QColor(255, 255, 0))
                painter.drawText(prefix_rect.topLeft(), prefix_text)


# ---- Global instance registry ----
_overlay_instance = None

def _register_overlay(tool):
    global _overlay_instance
    _overlay_instance = tool
    _log("_overlay_instance set")

def get_overlay():
    return _overlay_instance
