try:
    from plover.engine import StenoEngine
except ImportError:
    StenoEngine = None

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect, QMetaObject, Qt, Q_ARG
from .mouse_control import MouseControl
from .hints import HintManager
import os
import threading

# Debug log
_DEBUG_LOG = os.path.join(os.path.expanduser("~"), "plover_mouse_debug.log")

def _log(msg):
    try:
        with open(_DEBUG_LOG, "a") as f:
            tid = threading.current_thread().name
            f.write(f"[{tid}] {msg}\n")
    except:
        pass

# State
_current_rect = None
_is_dragging = False
_hint_manager = HintManager()
_hint_labels = ""

def _get_overlay():
    """Get the overlay tool instance (created by Plover's GUI system on the main thread)."""
    from .overlay_tool import get_overlay
    overlay = get_overlay()
    if overlay is None:
        _log("WARNING: Overlay tool not yet created. Open it from Tools menu first.")
    return overlay

def mm_init(engine: StenoEngine, args: str):
    _log("mm_init called")

def mn_grid(engine: StenoEngine, args: str):
    global _current_rect
    _log(f"mn_grid args='{args}', thread={threading.current_thread().name}")
    
    overlay = _get_overlay()
    if overlay is None:
        _log("ERROR: overlay is None, can't show grid")
        return

    app = QApplication.instance()
    screen = app.primaryScreen() if app else None
    if screen:
        screen_rect = screen.geometry()
    else:
        screen_rect = QRect(0, 0, 1920, 1080)
    
    if _current_rect is None or args == "reset":
        _current_rect = QRect(screen_rect)
        rect_copy = QRect(_current_rect)
        QMetaObject.invokeMethod(overlay, "show_grid", Qt.QueuedConnection, Q_ARG(QRect, rect_copy))
        return

    if args == "up":
        _current_rect.setHeight(_current_rect.height() // 2)
    elif args == "down":
        _current_rect.setTop(_current_rect.top() + _current_rect.height() // 2)
    elif args == "left":
        _current_rect.setWidth(_current_rect.width() // 2)
    elif args == "right":
        _current_rect.setLeft(_current_rect.left() + _current_rect.width() // 2)
    elif args == "close":
        QMetaObject.invokeMethod(overlay, "hide_grid", Qt.QueuedConnection)
        _current_rect = None
        return

    rect_copy = QRect(_current_rect)
    QMetaObject.invokeMethod(overlay, "show_grid", Qt.QueuedConnection, Q_ARG(QRect, rect_copy))
    MouseControl.move_to(_current_rect.center().x(), _current_rect.center().y())

def mn_click(engine: StenoEngine, args: str):
    global _current_rect
    button = args if args else 'left'
    MouseControl.click(button)
    
    if _current_rect is not None:
        overlay = _get_overlay()
        if overlay:
            QMetaObject.invokeMethod(overlay, "hide_grid", Qt.QueuedConnection)
        _current_rect = None

def mn_right_click(engine: StenoEngine, args: str):
    mn_click(engine, 'right')

def mn_move(engine: StenoEngine, args: str):
    try:
        dx, dy = map(int, args.split(','))
        MouseControl.nudge(dx, dy)
    except:
        pass

def mn_hint(engine: StenoEngine, args: str):
    global _hint_labels
    
    overlay = _get_overlay()
    if overlay is None:
        return
    
    if args == "start":
        hints = _hint_manager.scan_screen()
        _hint_labels = ""
        _log(f"mn_hint start: {len(hints)} hints found")
        if hints:
            overlay.hints = hints
            QMetaObject.invokeMethod(overlay, "show", Qt.QueuedConnection)
            QMetaObject.invokeMethod(overlay, "raise_", Qt.QueuedConnection)
            QMetaObject.invokeMethod(overlay, "update", Qt.QueuedConnection)
        return
        
    if args == "close":
        overlay.hints = []
        QMetaObject.invokeMethod(overlay, "update", Qt.QueuedConnection)
        QMetaObject.invokeMethod(overlay, "hide", Qt.QueuedConnection)
        _hint_manager.clear()
        _hint_labels = ""
        return
        
    if args.isalpha():
        _hint_labels = _hint_labels + args.upper()
        coord = _hint_manager.get_coordinate(_hint_labels)
        if coord:
            MouseControl.move_to(coord[0], coord[1])
            MouseControl.click('left')
            overlay.hints = []
            QMetaObject.invokeMethod(overlay, "update", Qt.QueuedConnection)
            QMetaObject.invokeMethod(overlay, "hide", Qt.QueuedConnection)
            _hint_manager.clear()
            _hint_labels = ""

def mn_toggle_drag(engine: StenoEngine, args: str):
    global _is_dragging
    if _is_dragging:
        MouseControl.release('left')
        _is_dragging = False
    else:
        MouseControl.press('left')
        _is_dragging = True
