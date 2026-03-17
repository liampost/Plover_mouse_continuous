import sys
import math

# Fix COM threading issues with PySide6
sys.coinit_flags = 2
import pywinauto
from pywinauto.findwindows import find_windows
from pywinauto.application import Application

class HintManager:
    def __init__(self):
        self.current_hints = {} # Maps label -> (x, y)
        self.letters = "abcdefghijklmnopqrstuvwxyz"

    def _generate_label(self, index, total):
        # Generates sequence a, b, c... aa, ab, ac...
        if total <= len(self.letters):
            return self.letters[index]
        
        # If we need two letters
        first = index // len(self.letters)
        second = index % len(self.letters)
        if first == 0:
            return self.letters[second]
        return self.letters[first - 1] + self.letters[second]

    def scan_screen(self, screen_rect=None):
        """Scan for clickable UI elements.
        
        Args:
            screen_rect: Optional tuple (left, top, right, bottom) to filter 
                         elements to a specific monitor's bounds.
        """
        self.current_hints.clear()
        
        # Connect to Desktop to see all windows
        desktop = pywinauto.Desktop(backend="uia")
        
        # Getting all visible top-level windows
        windows = desktop.windows(visible_only=True)
        
        clickable_elements = []
        
        for win in windows:
            # Skip irrelevant windows
            title = win.window_text()
            if not title or title in ["Mouse Overlay", "OverlayWindow", "Program Manager", "Task Manager"]:
                continue
                
            try:
                # Use a more targeted search: looking explicitly for interactive types
                controls = win.descendants(control_type="Button") + \
                           win.descendants(control_type="MenuItem") + \
                           win.descendants(control_type="ListItem") + \
                           win.descendants(control_type="Hyperlink") + \
                           win.descendants(control_type="TabItem")
                
                for control in controls:
                    try:
                        # Only grab if it is actually visible on screen and enabled
                        if control.is_visible() and control.is_enabled():
                            rect = control.rectangle()
                            if rect.width() > 0 and rect.height() > 0:
                                x = rect.left + rect.width() // 2
                                y = rect.top + rect.height() // 2
                                
                                # Filter to active screen bounds if specified
                                if screen_rect is not None:
                                    sl, st, sr, sb = screen_rect
                                    if x < sl or x > sr or y < st or y > sb:
                                        continue
                                
                                clickable_elements.append((x, y))
                    except:
                        pass
            except:
                pass

        # De-duplicate elements that are extremely close to each other
        unique_elements = []
        for ex, ey in clickable_elements:
            is_duplicate = False
            for ux, uy in unique_elements:
                if math.hypot(ex - ux, ey - uy) < 15:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_elements.append((ex, ey))

        hints_for_overlay = []
        total = len(unique_elements)
        
        for i, (x, y) in enumerate(unique_elements):
            label = self._generate_label(i, total)
            self.current_hints[label] = (x, y)
            hints_for_overlay.append((x, y, label))
            
        return hints_for_overlay

    def get_coordinate(self, label):
        return self.current_hints.get(label.lower())

    def clear(self):
        self.current_hints.clear()
