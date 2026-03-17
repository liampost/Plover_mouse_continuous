from plover_mousemaster.hints import HintManager
from plover_mousemaster.overlay import OverlayWindow
from PyQt5.QtWidgets import QApplication
import sys

def test_hints():
    app = QApplication(sys.argv)
    
    # 1. Test scanning
    print("Testing scanning...")
    hm = HintManager()
    hints = hm.scan_screen()
    
    print(f"Found {len(hints)} clickable elements!")
    if hints:
        print("First 5 hints:", hints[:5])
        
    # 2. Test overlay drawing
    print("Testing overlay display...")
    window = OverlayWindow()
    window.set_hints(hints)
    
    # Run loop to see it
    print("Close the window or press Ctrl+C to exit.")
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_hints()
