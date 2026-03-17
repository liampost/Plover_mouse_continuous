try:
    from plover.engine import StenoEngine
except ImportError:
    StenoEngine = None

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect, QMetaObject, Qt, Q_ARG
from PySide6.QtGui import QCursor
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

def _get_overlay():
    """Get the overlay tool instance."""
    from .overlay_tool import get_overlay
    overlay = get_overlay()
    if overlay is None:
        _log("WARNING: Overlay tool not yet created. Open it from Tools menu first.")
    return overlay

def _get_active_screen_rect():
    """Get the geometry of the screen where the mouse cursor currently is."""
    cursor_pos = QCursor.pos()
    app = QApplication.instance()
    if app:
        screen = app.screenAt(cursor_pos)
        if screen:
            return screen.geometry()
    if app:
        screen = app.primaryScreen()
        if screen:
            return screen.geometry()
    return QRect(0, 0, 1920, 1080)

def mm_init(engine: StenoEngine, args: str):
    _log("mm_init called")

def mn_grid(engine: StenoEngine, args: str):
    global _current_rect
    _log(f"mn_grid args='{args}', thread={threading.current_thread().name}")
    
    overlay = _get_overlay()
    if overlay is None:
        return

    # Use the screen where cursor currently is
    screen_rect = _get_active_screen_rect()
    
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
    """Move mouse by dx,dy pixels. Usage: {plover:mm_move:10,0}"""
    try:
        dx, dy = map(int, args.split(','))
        MouseControl.nudge(dx, dy)
    except:
        pass

def mn_scroll(engine: StenoEngine, args: str):
    """Scroll the mouse wheel. Usage: {plover:mm_scroll:up}, {plover:mm_scroll:down:5}
    
    Args format: direction or direction:clicks
    Directions: up, down, left, right
    Default clicks: 3
    """
    parts = args.split(':') if ':' in args else args.split(',')
    direction = parts[0].strip().lower() if parts else 'down'
    clicks = 3
    if len(parts) > 1:
        try:
            clicks = int(parts[1].strip())
        except:
            pass
    
    if direction in ('up', 'down', 'left', 'right'):
        MouseControl.scroll(clicks=clicks, direction=direction)
        _log(f"Scrolled {direction} by {clicks}")

def mn_screen(engine: StenoEngine, args: str):
    """Cycle through available screens and move cursor to center."""
    app = QApplication.instance()
    if not app:
        return
    
    screens = app.screens()
    if len(screens) <= 1:
        return
    
    cursor_pos = QCursor.pos()
    current_screen = app.screenAt(cursor_pos)
    
    current_idx = 0
    for i, screen in enumerate(screens):
        if screen == current_screen:
            current_idx = i
            break
    
    next_idx = (current_idx + 1) % len(screens)
    next_screen = screens[next_idx]
    next_center = next_screen.geometry().center()
    
    _log(f"Switching from screen {current_idx} to {next_idx}: center={next_center}")
    MouseControl.move_to(next_center.x(), next_center.y())

def mn_hint(engine: StenoEngine, args: str):
    """Start or close hint mode."""
    overlay = _get_overlay()
    if overlay is None:
        return
    
    if args == "start":
        screen_rect = _get_active_screen_rect()
        screen_bounds = (screen_rect.left(), screen_rect.top(), 
                         screen_rect.right(), screen_rect.bottom())
        
        hints = _hint_manager.scan_screen(screen_rect=screen_bounds)
        _log(f"mn_hint start: {len(hints)} hints found on active screen")
        
        if hints:
            overlay._hint_manager = _hint_manager
            overlay.all_hints = hints
            QMetaObject.invokeMethod(overlay, "activate_hints", Qt.QueuedConnection)
        return
        
    if args == "close":
        QMetaObject.invokeMethod(overlay, "deactivate_hints", Qt.QueuedConnection)
        _hint_manager.clear()
        return

def mn_toggle_drag(engine: StenoEngine, args: str):
    global _is_dragging
    if _is_dragging:
        MouseControl.release('left')
        _is_dragging = False
    else:
        MouseControl.press('left')
        _is_dragging = True
