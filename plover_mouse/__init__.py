import json
import os
import threading
import time
from typing import Dict, Tuple, List

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
    x = INPUT(type=INPUT_MOUSE, union=INPUT_UNION(mi=MOUSEINPUT(int(dx), int(dy), int(data), int(flags), 0, None)))
    ctypes.windll.user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

# --- Standard Plover Commands for Clicking ---

def mouse_press(engine: StenoEngine, args: str):
    args = args.strip().lower()
    flag = MOUSEEVENTF_LEFTDOWN
    if args == 'right': flag = MOUSEEVENTF_RIGHTDOWN
    elif args == 'middle': flag = MOUSEEVENTF_MIDDLEDOWN
    _send_mouse_input(flag)

def mouse_release(engine: StenoEngine, args: str):
    args = args.strip().lower()
    flag = MOUSEEVENTF_LEFTUP
    if args == 'right': flag = MOUSEEVENTF_RIGHTUP
    elif args == 'middle': flag = MOUSEEVENTF_MIDDLEUP
    _send_mouse_input(flag)

def mouse_click(engine: StenoEngine, args: str):
    args2 = args.split(",")
    args2 = [x.strip().lower() for x in args2] + [""] * (2 - len(args2))
    btn = args2[0]
    clicks = 1 if(args2[1] == "") else int(args2[1])
    
    down_flag = MOUSEEVENTF_LEFTDOWN
    up_flag = MOUSEEVENTF_LEFTUP
    if btn == 'right':
        down_flag, up_flag = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    elif btn == 'middle':
        down_flag, up_flag = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP

    for _ in range(clicks):
        _send_mouse_input(down_flag)
        _send_mouse_input(up_flag)

# --- Extention Plugin for Continuous Movement ---

class PloverMouseExtension:
    """
    A Plover Extension plugin that intercepts raw QWERTY keys to provide
    smooth, continuous mouse movement and scrolling while the keys are held down.
    Allows specifying modifier keys that must be held to activate movement.
    """

    def __init__(self, engine: StenoEngine):
        self.engine = engine
        self._running = False
        self._thread = None
        self._listener = None
        
        self.active_dx = 0
        self.active_dy = 0
        self.active_scroll_y = 0

        # Physical QWERTY to vector mappings (dx, dy, scroll_dy)
        self.key_map: Dict[str, Tuple[int, int, int]] = {
            'h': (0, -5, 0),  # Right Hand R (-R) = Up
            'u': (0, 5, 0),   # Right Hand P (-P) = Down
            'j': (-5, 0, 0),  # Right Hand B (-B) = Left
            'k': (5, 0, 0),   # Right Hand G (-G) = Right
        }
        
        # Keys that MUST be held down to activate movement
        # e.g., 'a' (S), 's' (K), 'e' (P), 'f' (R) for left hand SKPR
        self.modifier_keys: List[str] = ['a', 's', 'e', 'f']

        self.pressed_keys = set()
        
        self.load_config()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'mouse_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    if "modifiers" in data:
                        self.modifier_keys = data["modifiers"]
                    if "keys" in data:
                        self.key_map = {k: tuple(v) for k, v in data["keys"].items()}
            except Exception as e:
                print(f"Plover Mouse: Error loading config {e}")
        else:
            try:
                with open(config_path, 'w') as f:
                    json.dump({
                        "modifiers": self.modifier_keys,
                        "keys": {k: list(v) for k,v in self.key_map.items()}
                    }, f, indent=4)
            except:
                pass

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._movement_loop, daemon=True)
        self._thread.start()
        self._listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self._listener.start()

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()
        if self._thread:
            self._thread.join(timeout=1.0)
            
    def _modifiers_active(self) -> bool:
        if not self.modifier_keys:
            return True
        return all(mod in self.pressed_keys for mod in self.modifier_keys)

    def on_press(self, key):
        try:
            char = key.char.lower()
            if char not in self.pressed_keys:
                self.pressed_keys.add(char)
                if char in self.key_map:
                    dx, dy, sdy = self.key_map[char]
                    self.active_dx += dx
                    self.active_dy += dy
                    self.active_scroll_y += sdy
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            char = key.char.lower()
            if char in self.pressed_keys:
                self.pressed_keys.remove(char)
                if char in self.key_map:
                    dx, dy, sdy = self.key_map[char]
                    self.active_dx -= dx
                    self.active_dy -= dy
                    self.active_scroll_y -= sdy
        except AttributeError:
            pass

    def _movement_loop(self):
        while self._running:
            if self._modifiers_active():
                if self.active_dx != 0 or self.active_dy != 0:
                    _send_mouse_input(MOUSEEVENTF_MOVE, dx=self.active_dx, dy=self.active_dy)
                
                if self.active_scroll_y != 0:
                    _send_mouse_input(MOUSEEVENTF_WHEEL, data=self.active_scroll_y * 15)
                
            time.sleep(0.01)


