try:
    from plover.engine import StenoEngine
except ImportError:
    StenoEngine = None

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect, QObject, pyqtSignal, pyqtSlot, Qt
from PyQt5 import sip
from .mouse_control import MouseControl
from .hints import HintManager
import sys

# Singleton-like state management
_current_rect = None
_is_dragging = False
_hint_manager = HintManager()
_hint_labels = ""

class OverlayController(QObject):
    show_grid_signal = pyqtSignal(QRect)
    hide_grid_signal = pyqtSignal()
    show_hints_signal = pyqtSignal(list)
    hide_hints_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.overlay = None
        self.show_grid_signal.connect(self.do_show_grid, Qt.QueuedConnection)
        self.hide_grid_signal.connect(self.do_hide_grid, Qt.QueuedConnection)
        self.show_hints_signal.connect(self.do_show_hints, Qt.QueuedConnection)
        self.hide_hints_signal.connect(self.do_hide_hints, Qt.QueuedConnection)

    @pyqtSlot(QRect)
    def do_show_grid(self, rect):
        from .overlay import OverlayWindow
        if self.overlay is None or sip.isdeleted(self.overlay):
            self.overlay = OverlayWindow()
        self.overlay.show_grid(rect)

    @pyqtSlot()
    def do_hide_grid(self):
        if self.overlay and not sip.isdeleted(self.overlay):
            self.overlay.hide_grid()

    @pyqtSlot(list)
    def do_show_hints(self, hints):
        from .overlay import OverlayWindow
        if self.overlay is None or sip.isdeleted(self.overlay):
            self.overlay = OverlayWindow()
        self.overlay.set_hints(hints)

    @pyqtSlot()
    def do_hide_hints(self):
        if self.overlay and not sip.isdeleted(self.overlay):
            self.overlay.hints = []
            self.overlay.update()
            self.overlay.hide()

# Initialize controller at module level (loads on main thread during Plover startup)
_controller = None

def _get_controller():
    global _controller
    if _controller is None:
        _controller = OverlayController()
        app = QApplication.instance()
        if app is not None:
            _controller.moveToThread(app.thread())
    return _controller

def mm_init(engine: StenoEngine, args: str):
    _get_controller()

def mn_grid(engine: StenoEngine, args: str):
    global _current_rect
    controller = _get_controller()
    
    app = QApplication.instance()
    screen = app.primaryScreen() if app else None
    if screen:
        screen_rect = screen.geometry()
    else:
        screen_rect = QRect(0, 0, 1920, 1080)
    
    if _current_rect is None or args == "reset":
        _current_rect = QRect(screen_rect)
        controller.show_grid_signal.emit(_current_rect)
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
        controller.hide_grid_signal.emit()
        _current_rect = None
        return

    controller.show_grid_signal.emit(_current_rect)
    MouseControl.move_to(_current_rect.center().x(), _current_rect.center().y())

def mn_click(engine: StenoEngine, args: str):
    global _current_rect
    button = args if args else 'left'
    MouseControl.click(button)
    
    if _current_rect is not None:
        _get_controller().hide_grid_signal.emit()
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
    controller = _get_controller()
    
    if args == "start":
        # Scan screen and show hints
        hints = _hint_manager.scan_screen()
        _hint_labels = ""
        if hints:
            controller.show_hints_signal.emit(hints)
        return
        
    if args == "close":
        controller.hide_hints_signal.emit()
        _hint_manager.clear()
        _hint_labels = ""
        return
        
    # Otherwise, args is a letter being typed
    if args.isalpha():
        _hint_labels = _hint_labels + args.upper()
        coord = _hint_manager.get_coordinate(_hint_labels)
        if coord:
            # We found a match! Move and click
            MouseControl.move_to(coord[0], coord[1])
            MouseControl.click('left')
            # Hide hints automatically
            controller.hide_hints_signal.emit()
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

