import sys
import math
import ctypes
import ctypes.wintypes

# Fix COM threading issues
sys.coinit_flags = 2
import pywinauto

class HintManager:
    """UI element discovery matching MouseMaster's approach:
    - Only scan the FOREGROUND window (not all desktop windows)
    - Filter by interaction patterns (invokable, focusable, toggleable, etc.)
    - 40px dedup distance
    - Clip elements to their parent window bounds
    """
    def __init__(self):
        self.current_hints = {}  # Maps label -> (x, y)
        self.letters = "abcdefghijklmnopqrstuvwxyz"

    def _generate_labels(self, count):
        """Generate uniform-length labels to prevent collisions."""
        if count == 0:
            return []
        
        labels = []
        if count <= 26:
            # Two-letter labels: aa, ab, ac...
            for i in range(count):
                labels.append(self.letters[0] + self.letters[i])
        else:
            # Two-letter combos: aa, ab, ... az, ba, bb, ...
            for i in range(min(count, 676)):
                first = i // 26
                second = i % 26
                labels.append(self.letters[first] + self.letters[second])
        
        return labels

    def _get_foreground_window_handle(self):
        """Get the handle of the foreground window, like MouseMaster does."""
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        return hwnd
    
    def _get_window_rect(self, hwnd):
        """Get the bounding rect of a window."""
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top, rect.right, rect.bottom)

    def scan_screen(self, screen_rect=None):
        """Scan for clickable UI elements using MouseMaster's approach.
        
        Key differences from previous approach:
        - Only scans the FOREGROUND window (active window)
        - Uses pywinauto to check interaction patterns
        - Filters: is_visible, is_enabled, and has an invocable/toggleable/focusable pattern
        - 40px dedup distance (matching MouseMaster)
        - Clips elements to window bounds
        """
        self.current_hints.clear()
        
        # Get the foreground window (like MouseMaster's GetForegroundWindow)
        hwnd = self._get_foreground_window_handle()
        if not hwnd:
            return []
        
        try:
            app = pywinauto.Application(backend="uia").connect(handle=hwnd)
            win = app.window(handle=hwnd).wrapper_object()
        except Exception:
            return []
        
        win_rect = self._get_window_rect(hwnd)
        win_left, win_top, win_right, win_bottom = win_rect
        
        clickable_elements = []
        
        try:
            # Get ALL descendants, then filter by interaction patterns
            # This matches MouseMaster's approach of using pattern-based filtering
            all_controls = win.descendants()
            
            for control in all_controls:
                try:
                    if not control.is_visible() or not control.is_enabled():
                        continue
                    
                    # Check interaction patterns (matching MouseMaster's condition):
                    # IsKeyboardFocusable OR IsInvokePatternAvailable OR 
                    # ControlType=Button OR IsExpandCollapsePatternAvailable OR
                    # IsTogglePatternAvailable OR IsSelectionItemPatternAvailable
                    is_interactive = False
                    
                    try:
                        ctrl_type = control.element_info.control_type
                        if ctrl_type in ("Button", "MenuItem", "Hyperlink", 
                                         "TabItem", "CheckBox", "RadioButton",
                                         "ComboBox", "SplitButton"):
                            is_interactive = True
                    except:
                        pass
                    
                    if not is_interactive:
                        try:
                            # Check if keyboard focusable
                            if control.is_keyboard_focusable():
                                is_interactive = True
                        except:
                            pass
                    
                    if not is_interactive:
                        try:
                            # Check for invoke pattern
                            iface = control.iface_invoke
                            if iface is not None:
                                is_interactive = True
                        except:
                            pass
                    
                    if not is_interactive:
                        try:
                            # Check for toggle pattern
                            iface = control.iface_toggle
                            if iface is not None:
                                is_interactive = True
                        except:
                            pass
                    
                    if not is_interactive:
                        try:
                            # Check for expand/collapse pattern
                            iface = control.iface_expand_collapse
                            if iface is not None:
                                is_interactive = True
                        except:
                            pass
                    
                    if not is_interactive:
                        try:
                            # Check for selection item pattern
                            iface = control.iface_selection_item
                            if iface is not None:
                                is_interactive = True
                        except:
                            pass
                    
                    if not is_interactive:
                        continue
                    
                    rect = control.rectangle()
                    w = rect.width()
                    h = rect.height()
                    
                    if w <= 0 or h <= 0:
                        continue
                    
                    x = rect.left + w // 2
                    y = rect.top + h // 2
                    
                    # Clip to parent window bounds (like MouseMaster)
                    if x < win_left or x > win_right or y < win_top or y > win_bottom:
                        continue
                    
                    # Also clip to active screen if specified
                    if screen_rect is not None:
                        sl, st, sr, sb = screen_rect
                        if x < sl or x > sr or y < st or y > sb:
                            continue
                    
                    clickable_elements.append((x, y))
                except:
                    pass
        except:
            pass

        # De-duplicate with 40px distance (matching MouseMaster's MIN_DISTANCE_BETWEEN_HINTS)
        unique_elements = []
        for ex, ey in clickable_elements:
            is_duplicate = False
            for ux, uy in unique_elements:
                dx = ex - ux
                dy = ey - uy
                if dx * dx + dy * dy < 40 * 40:
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
