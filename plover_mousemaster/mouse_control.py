import ctypes
import time

# Windows Constants
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x01000

WHEEL_DELTA = 120

user32 = ctypes.windll.user32

class MouseControl:
    @staticmethod
    def move_to(x, y):
        user32.SetCursorPos(int(x), int(y))

    @staticmethod
    def get_position():
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    @staticmethod
    def click(button='left'):
        if button == 'left':
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif button == 'right':
            user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        elif button == 'middle':
            user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
            user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)

    @staticmethod
    def double_click():
        MouseControl.click()
        time.sleep(0.05)
        MouseControl.click()

    @staticmethod
    def press(button='left'):
        if button == 'left':
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        elif button == 'right':
            user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)

    @staticmethod
    def release(button='left'):
        if button == 'left':
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif button == 'right':
            user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

    @staticmethod
    def nudge(dx, dy):
        x, y = MouseControl.get_position()
        MouseControl.move_to(x + dx, y + dy)

    @staticmethod
    def scroll(clicks=3, direction='up'):
        """Scroll the mouse wheel.
        
        Args:
            clicks: Number of scroll increments (default 3)
            direction: 'up', 'down', 'left', or 'right'
        """
        if direction in ('up', 'down'):
            delta = WHEEL_DELTA * clicks if direction == 'up' else -WHEEL_DELTA * clicks
            user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, ctypes.c_ulong(delta & 0xFFFFFFFF), 0)
        elif direction in ('left', 'right'):
            delta = WHEEL_DELTA * clicks if direction == 'right' else -WHEEL_DELTA * clicks
            user32.mouse_event(MOUSEEVENTF_HWHEEL, 0, 0, ctypes.c_ulong(delta & 0xFFFFFFFF), 0)
