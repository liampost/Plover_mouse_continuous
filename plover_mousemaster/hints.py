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

    def _generate_labels(self, count):
        """Generate uniform-length labels for all hints.
        
        All labels will have the same length to prevent collisions
        (e.g. 'a' matching before 'ag').
        
        For <= 26 elements: aa, ab, ac... az
        For <= 676 elements: aa, ab, ac... zz
        """
        if count == 0:
            return []
        
        labels = []
        
        if count <= 26:
            # Use two-letter labels: aa, ab, ac... for uniform length
            for i in range(count):
                labels.append(self.letters[i] + self.letters[i])
            # Actually, that's weird (aa, bb, cc). Let's use: 
            # a + a, a + b, a + c ... so it's clearer
            labels = []
            for i in range(count):
                first = i // 26
                second = i % 26
                if count <= 26:
                    # For small sets, use single first letter + varied second
                    labels.append(self.letters[0] + self.letters[i])
                else:
                    labels.append(self.letters[first] + self.letters[second])
        else:
            # Two-letter combos: aa, ab, ac, ..., az, ba, bb, ...
            for i in range(min(count, 676)):
                first = i // 26
                second = i % 26
                labels.append(self.letters[first] + self.letters[second])
        
        return labels

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
            if not title or title in ["Mouse Overlay", "OverlayWindow", "Program Manager"]:
                continue
            
            # Skip windows that are too small to be real
            try:
                win_rect = win.rectangle()
                if win_rect.width() < 10 or win_rect.height() < 10:
                    continue
            except:
                continue
                
            try:
                # Use a targeted search for interactive control types
                controls = win.descendants(control_type="Button") + \
                           win.descendants(control_type="MenuItem") + \
                           win.descendants(control_type="Hyperlink") + \
                           win.descendants(control_type="TabItem")
                
                for control in controls:
                    try:
                        if not control.is_visible() or not control.is_enabled():
                            continue
                        
                        rect = control.rectangle()
                        w = rect.width()
                        h = rect.height()
                        
                        # Filter out too-small or too-large elements
                        if w < 5 or h < 5:
                            continue
                        if w > 800 or h > 400:
                            continue
                        
                        x = rect.left + w // 2
                        y = rect.top + h // 2
                        
                        # Filter to active screen bounds if specified
                        if screen_rect is not None:
                            sl, st, sr, sb = screen_rect
                            if x < sl or x > sr or y < st or y > sb:
                                continue
                        
                        # Check that the element has a name or automation ID
                        # (elements without names are often invisible decorators)
                        name = control.window_text()
                        auto_id = ""
                        try:
                            auto_id = control.automation_id()
                        except:
                            pass
                        
                        if not name and not auto_id:
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
                if math.hypot(ex - ux, ey - uy) < 20:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_elements.append((ex, ey))

        # Generate uniform-length labels
        labels = self._generate_labels(len(unique_elements))
        
        hints_for_overlay = []
        for i, (x, y) in enumerate(unique_elements):
            label = labels[i]
            self.current_hints[label] = (x, y)
            hints_for_overlay.append((x, y, label))
            
        return hints_for_overlay

    def get_coordinate(self, label):
        return self.current_hints.get(label.lower())

    def get_matching_labels(self, prefix):
        """Return all labels that start with the given prefix."""
        prefix = prefix.lower()
        return [label for label in self.current_hints if label.startswith(prefix)]

    def clear(self):
        self.current_hints.clear()
