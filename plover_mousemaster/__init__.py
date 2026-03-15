import subprocess
import os
from plover.engine import StenoEngine

MOUSEMASTER_EXE = r"C:\Users\postw\OneDrive\Documents\Coding\MISC\Plover_plugins\mousemaster.exe"
_mm_process = None

def mm_init(engine: StenoEngine, args: str):
    global _mm_process
    
    if _mm_process and _mm_process.poll() is None:
        return
        
    if os.path.exists(MOUSEMASTER_EXE):
        try:
            _mm_process = subprocess.Popen([MOUSEMASTER_EXE], cwd=os.path.dirname(MOUSEMASTER_EXE), 
                                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        except Exception as e:
            print(f"Failed to start MouseMaster: {e}")

def _send_combo(engine: StenoEngine, combo: str):
    engine._keyboard_emulation.send_key_combination(combo)

def mm_normal(engine: StenoEngine, args: str): _send_combo(engine, "alt_l(e)")
def mm_hint(engine: StenoEngine, args: str): _send_combo(engine, "f")
def mm_grid(engine: StenoEngine, args: str): _send_combo(engine, "g")
def mm_screen(engine: StenoEngine, args: str): _send_combo(engine, "c")
def mm_left_click(engine: StenoEngine, args: str): _send_combo(engine, ";")
def mm_right_click(engine: StenoEngine, args: str): _send_combo(engine, "'")
def mm_toggle_click(engine: StenoEngine, args: str): _send_combo(engine, "n")
def mm_nav_back(engine: StenoEngine, args: str): _send_combo(engine, "h")
def mm_nav_forward(engine: StenoEngine, args: str): _send_combo(engine, "y")
def mm_click_disable(engine: StenoEngine, args: str): _send_combo(engine, ".")
def mm_disable(engine: StenoEngine, args: str): _send_combo(engine, "q")
