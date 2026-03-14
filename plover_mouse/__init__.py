import json
import os
import threading
import time
from typing import Dict, Tuple

from pynput import keyboard
from plover.engine import StenoEngine

import ctypes
from ctypes import wintypes

# --- Windows ctypes structures for SendInput ---
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p))

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD))

class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p))

class INPUT_UNION(ctypes.Union):
    _fields_ = (("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT))

class INPUT(ctypes.Structure):
    _fields_ = (("type", wintypes.DWORD),
                ("union", INPUT_UNION))

def _send_mouse_input(flags, dx=0, dy=0, data=0):
    x = INPUT(type=INPUT_MOUSE, union=INPUT_UNION(mi=MOUSEINPUT(dx, dy, data, flags, 0, None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

class PloverMouseExtension:
    """
    A Plover Extension plugin that intercepts raw QWERTY keys to provide
    smooth, continuous mouse movement and scrolling while the keys are held down.
    """

    def __init__(self, engine: StenoEngine):
        self.engine = engine
        self._running = False
        self._thread = None
        self._listener = None
        
        # Current aggregated deltas based on keys currently held down
        self.active_dx = 0
        self.active_dy = 0
        self.active_scroll_y = 0

        # Physical QWERTY to vector mappings (Customizable)
        # Default mapping:
        # e: Up, d: Down, s: Left, f: Right 
        # (These are common left-hand resting keys, adjust as needed)
        self.key_map: Dict[str, Tuple[int, int, int]] = {
            'e': (0, -5, 0),  # dx, dy, scroll_dy
            'd': (0, 5, 0),
            's': (-5, 0, 0),
            'f': (5, 0, 0),
            'r': (0, 0, 1),   # Scroll Up
            'v': (0, 0, -1)   # Scroll Down
        }

        # Track keys currently pressed to avoid compounding speeds from OS auto-repeat
        self.pressed_keys = set()
        
        self.load_config()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'mouse_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    # Convert str keys and list values to proper formats
                    loaded_map = json.load(f)
                    self.key_map = {k: tuple(v) for k, v in loaded_map.items()}
            except Exception as e:
                print(f"Plover Mouse: Error loading config {e}")
        else:
            # Create default config if it doesn't exist
            try:
                with open(config_path, 'w') as f:
                    json.dump({k: list(v) for k,v in self.key_map.items()}, f, indent=4)
            except:
                pass

    def start(self):
        self._running = True
        
        # Start the background movement thread
        self._thread = threading.Thread(target=self._movement_loop, daemon=True)
        self._thread.start()
        
        # Start the global keyboard listener
        self._listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release)
        self._listener.start()

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()
        if self._thread:
            self._thread.join(timeout=1.0)

    def on_press(self, key):
        try:
            char = key.char.lower()
            if char in self.key_map and char not in self.pressed_keys:
                self.pressed_keys.add(char)
                dx, dy, sdy = self.key_map[char]
                self.active_dx += dx
                self.active_dy += dy
                self.active_scroll_y += sdy
        except AttributeError:
            pass # Non-character keys

    def on_release(self, key):
        try:
            char = key.char.lower()
            if char in self.key_map and char in self.pressed_keys:
                self.pressed_keys.remove(char)
                dx, dy, sdy = self.key_map[char]
                self.active_dx -= dx
                self.active_dy -= dy
                self.active_scroll_y -= sdy
        except AttributeError:
            pass

    def _movement_loop(self):
        """Background thread that continuously applies movement based on active deltas."""
        while self._running:
            if self.active_dx != 0 or self.active_dy != 0:
                _send_mouse_input(MOUSEEVENTF_MOVE, dx=self.active_dx, dy=self.active_dy)
            
            if self.active_scroll_y != 0:
                # Scroll amount multiplier (120 per click standard)
                _send_mouse_input(MOUSEEVENTF_WHEEL, data=self.active_scroll_y * 15)
                
            time.sleep(0.01) # 100fps movement for smoothness

