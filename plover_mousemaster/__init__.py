try:
    from plover.engine import StenoEngine
except ImportError:
    StenoEngine = None

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect
from PyQt5 import sip
from .overlay import OverlayWindow
from .mouse_control import MouseControl
import sys

# Singleton-like state management
_overlay = None
_current_rect = None
_is_dragging = False

def get_overlay():
    global _overlay
    if _overlay is None or sip.isdeleted(_overlay):
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        _overlay = OverlayWindow()
    return _overlay

def mm_init(engine: StenoEngine, args: str):
    # For the native plugin, init just ensures the overlay is ready.
    # It doesn't need to launch an external .exe anymore!
    get_overlay()

def mn_grid(engine: StenoEngine, args: str):
    global _current_rect
    overlay = get_overlay()
    
    screen = QApplication.primaryScreen()
    if screen:
        screen_rect = screen.geometry()
    else:
        screen_rect = QRect(0, 0, 1920, 1080)
    
    if _current_rect is None or args == "reset":
        _current_rect = QRect(screen_rect)
        overlay.show_grid(_current_rect)
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
        overlay.hide_grid()
        _current_rect = None
        return

    overlay.show_grid(_current_rect)
    MouseControl.move_to(_current_rect.center().x(), _current_rect.center().y())

def mn_click(engine: StenoEngine, args: str):
    global _current_rect
    button = args if args else 'left'
    MouseControl.click(button)
    
    if _current_rect is not None:
        get_overlay().hide_grid()
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
    # Hint mode logic to be implemented
    pass

def mn_toggle_drag(engine: StenoEngine, args: str):
    global _is_dragging
    if _is_dragging:
        MouseControl.release('left')
        _is_dragging = False
    else:
        MouseControl.press('left')
        _is_dragging = True
