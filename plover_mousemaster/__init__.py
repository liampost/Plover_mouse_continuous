import subprocess
import os
import ctypes
from plover.engine import StenoEngine

MOUSEMASTER_LAUNCHER = r"C:\Users\postw\OneDrive\Documents\Coding\MISC\Plover_plugins\mousemaster_launcher.vbs"

def mm_init(engine: StenoEngine, args: str):
    if os.path.exists(MOUSEMASTER_LAUNCHER):
        try:
            cwd = os.path.dirname(MOUSEMASTER_LAUNCHER)
            original_cwd = os.getcwd()
            os.chdir(cwd)
            os.startfile(MOUSEMASTER_LAUNCHER)
            os.chdir(original_cwd)
        except Exception as e:
            print(f"Failed to start MouseMaster Launcher: {e}")

import time

def _send_vk(vk_code):
    scan_code = ctypes.windll.user32.MapVirtualKeyA(vk_code, 0)
    # key down
    ctypes.windll.user32.keybd_event(vk_code, scan_code, 0, 0)
    time.sleep(0.01)
    # key up
    ctypes.windll.user32.keybd_event(vk_code, scan_code, 2, 0)

# F13 = 0x7C, F14 = 0x7D, F15 = 0x7E, F16 = 0x7F, F17 = 0x80, F18 = 0x81, F19 = 0x82, F20 = 0x83, F21 = 0x84, F22 = 0x85, F23 = 0x86
def mm_normal(engine: StenoEngine, args: str): _send_vk(0x7C)
def mm_hint(engine: StenoEngine, args: str): _send_vk(0x7D)
def mm_grid(engine: StenoEngine, args: str): _send_vk(0x7E)
def mm_screen(engine: StenoEngine, args: str): _send_vk(0x7F)
def mm_left_click(engine: StenoEngine, args: str): _send_vk(0x80)
def mm_right_click(engine: StenoEngine, args: str): _send_vk(0x81)
def mm_toggle_click(engine: StenoEngine, args: str): _send_vk(0x82)
def mm_nav_back(engine: StenoEngine, args: str): _send_vk(0x83)
def mm_nav_forward(engine: StenoEngine, args: str): _send_vk(0x84)
def mm_click_disable(engine: StenoEngine, args: str): _send_vk(0x85)
def mm_disable(engine: StenoEngine, args: str): _send_vk(0x86)
