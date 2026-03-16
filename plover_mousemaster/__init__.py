import subprocess
import os
import ctypes
from plover.engine import StenoEngine

MOUSEMASTER_EXE = r"C:\Users\postw\OneDrive\Documents\Coding\MISC\Plover_plugins\mousemaster.exe"
_mm_process = None

def mm_init(engine: StenoEngine, args: str):
    # Check if MouseMaster is already running using Windows tasklist
    try:
        output = subprocess.check_output('tasklist /FI "IMAGENAME eq mousemaster.exe"', shell=True).decode()
        if 'mousemaster.exe' in output.lower():
            # Already running, do nothing
            return
    except subprocess.CalledProcessError:
        pass
        
    if os.path.exists(MOUSEMASTER_EXE):
        try:
            cwd = os.path.dirname(MOUSEMASTER_EXE)
            original_cwd = os.getcwd()
            os.chdir(cwd)
            os.startfile(MOUSEMASTER_EXE)
            os.chdir(original_cwd)
        except Exception as e:
            print(f"Failed to start MouseMaster: {e}")

def _send_vk(vk_code):
    # key down
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    # key up
    ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)

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
