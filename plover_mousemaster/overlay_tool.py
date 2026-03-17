"""
Overlay Tool - A plover.gui_qt.tool.Tool subclass that manages the transparent overlay.
This runs on Plover's main GUI thread, so all Qt rendering works correctly.
Plover 5.1.0 uses PySide6 (not PyQt5).
"""
from plover.engine import StenoEngine
from plover.gui_qt.tool import Tool

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QRect, Slot
from PySide6.QtGui import QPainter, QPen, QColor, QFont

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

        self.grid_visible = False
        self.grid_rect = QRect()
        self.hints = []  # List of (x, y, label)

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

        # Full screen size
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        else:
            self.setGeometry(0, 0, 1920, 1080)

        # Register globally so command plugins can find us
        _register_overlay(self)
        _log("OverlayTool registered globally")

    @Slot(QRect)
    def show_grid(self, rect):
        _log(f"show_grid called, rect={rect}, thread={threading.current_thread().name}")
        self.grid_rect = rect
        self.grid_visible = True
        self.show()
        self.raise_()
        self.update()
        _log(f"After show_grid: visible={self.isVisible()}")

    @Slot()
    def hide_grid(self):
        self.grid_visible = False
        self.hide()

    @Slot(list)
    def set_hints(self, hints):
        _log(f"set_hints called, count={len(hints)}, thread={threading.current_thread().name}")
        self.hints = hints
        self.show()
        self.raise_()
        self.update()
        _log(f"After set_hints: visible={self.isVisible()}")

    @Slot()
    def clear_hints(self):
        self.hints = []
        self.update()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.grid_visible:
            self._draw_grid(painter)

        if self.hints:
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

        for x, y, label in self.hints:
            text_rect = painter.fontMetrics().boundingRect(label)
            text_rect.moveCenter(QRect(x, y, 1, 1).center())
            text_rect.adjust(-5, -5, 5, 5)

            painter.setBrush(QColor(0, 0, 0, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRect(text_rect)

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
