import sys
import math
import ctypes
import ctypes.wintypes

# Fix COM threading issues
sys.coinit_flags = 2
import pywinauto

class HintManager:
    """UI element discovery matching MouseMaster's approach:
    - Scan the FOREGROUND window + the taskbar
    - Filter by interaction patterns (invokable, focusable, toggleable, etc.)
    - 40px dedup distance
    - Clip elements to their parent window bounds
    - Single-letter labels when ≤26, double when >26
    """
    def __init__(self):
        self.current_hints = {}  # Maps label -> (x, y)
        self.letters = "abcdefghijklmnopqrstuvwxyz"

    def _generate_labels(self, count):
        """Single letters when ≤26 elements, uniform double letters when >26."""
        if count == 0:
            return []
        
        if count <= 26:
            # Single-letter labels: a, b, c...
            return [self.letters[i] for i in range(count)]
        else:
            # Two-letter combos: aa, ab, ... az, ba, bb, ...
            labels = []
            for i in range(min(count, 676)):
                first = i // 26
                second = i % 26
                labels.append(self.letters[first] + self.letters[second])
            return labels

    def _get_foreground_window_handle(self):
        """Get the handle of the foreground window."""
        user32 = ctypes.windll.user32
        return user32.GetForegroundWindow()
    
    def _get_window_rect(self, hwnd):
        """Get the bounding rect of a window."""
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.left, rect.top, rect.right, rect.bottom)

    def _scan_window(self, win, win_rect, screen_rect, elements):
        """Scan a single window for interactive elements."""
        win_left, win_top, win_right, win_bottom = win_rect
        
        try:
            all_controls = win.descendants()
            
            for control in all_controls:
                try:
                    if not control.is_visible() or not control.is_enabled():
                        continue
                    
                    # Check interaction patterns (MouseMaster's filter)
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
                            if control.is_keyboard_focusable():
                                is_interactive = True
                        except:
                            pass
                    
                    if not is_interactive:
                        try:
                            if control.iface_invoke is not None:
                                is_interactive = True
                        except:
                            pass
                    
                    if not is_interactive:
                        try:
                            if control.iface_toggle is not None:
                                is_interactive = True
                        except:
                            pass
                    
                    if not is_interactive:
                        try:
                            if control.iface_expand_collapse is not None:
                                is_interactive = True
                        except:
                            pass
                    
                    if not is_interactive:
                        try:
                            if control.iface_selection_item is not None:
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
                    
                    # Clip to parent window bounds
                    if x < win_left or x > win_right or y < win_top or y > win_bottom:
                        continue
                    
                    # Clip to active screen if specified
                    if screen_rect is not None:
                        sl, st, sr, sb = screen_rect
                        if x < sl or x > sr or y < st or y > sb:
                            continue
                    
                    elements.append((x, y))
                except:
                    pass
        except:
            pass

    def scan_screen(self, screen_rect=None):
        """Scan for clickable UI elements."""
        self.current_hints.clear()
        clickable_elements = []
        
        # 1. Scan the foreground window
        hwnd = self._get_foreground_window_handle()
        if hwnd:
            try:
                app = pywinauto.Application(backend="uia").connect(handle=hwnd)
                win = app.window(handle=hwnd).wrapper_object()
                win_rect = self._get_window_rect(hwnd)
                self._scan_window(win, win_rect, screen_rect, clickable_elements)
            except:
                pass
        
        # 2. Also scan the taskbar
        try:
            desktop = pywinauto.Desktop(backend="uia")
            taskbar_windows = desktop.windows(class_name="Shell_TrayWnd")
            for taskbar in taskbar_windows:
                try:
                    tb_rect = taskbar.rectangle()
                    tb_bounds = (tb_rect.left, tb_rect.top, tb_rect.right, tb_rect.bottom)
                    self._scan_window(taskbar, tb_bounds, screen_rect, clickable_elements)
                except:
                    pass
            
            # Also scan secondary taskbars on other monitors
            secondary_taskbars = desktop.windows(class_name="Shell_SecondaryTrayWnd")
            for taskbar in secondary_taskbars:
                try:
                    tb_rect = taskbar.rectangle()
                    tb_bounds = (tb_rect.left, tb_rect.top, tb_rect.right, tb_rect.bottom)
                    self._scan_window(taskbar, tb_bounds, screen_rect, clickable_elements)
                except:
                    pass
        except:
            pass

        # De-duplicate with 40px distance
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

        # Generate labels (single if ≤26 elements, double if >26)
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
