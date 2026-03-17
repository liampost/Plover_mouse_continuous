"""
Overlay Diagnostic Script
Tests different PyQt5 window rendering methods to find what's visible.
Each test shows a window for 3 seconds, then moves to the next.
"""
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel
from PyQt5.QtCore import Qt, QRect, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
import sys
import time

class Test1_OpaqueWindow(QWidget):
    """Test 1: Plain opaque red window, no transparency at all"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TEST 1: Opaque Red Window")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: red;")

class Test2_SemiTransparentWindow(QWidget):
    """Test 2: Semi-transparent window using setWindowOpacity"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TEST 2: Semi-Transparent")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: red;")
        self.setWindowOpacity(0.7)

class Test3_FramelessOpaque(QWidget):
    """Test 3: Frameless + StaysOnTop but still opaque"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: red;")

class Test4_FramelessSemiTransparent(QWidget):
    """Test 4: Frameless + StaysOnTop + semi-transparent"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("background-color: red;")
        self.setWindowOpacity(0.5)

class Test5_TranslucentBackground(QWidget):
    """Test 5: WA_TranslucentBackground with painted content"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 400, 300)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Draw a semi-transparent red rectangle
        p.setBrush(QColor(255, 0, 0, 150))
        p.setPen(Qt.NoPen)
        p.drawRect(self.rect())
        # Draw white text
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Arial", 24, QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, "TEST 5\nTranslucent BG")

class Test6_ToolWindow(QWidget):
    """Test 6: Tool window + Translucent (closest to what we need)"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(100, 100, 400, 300)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(255, 0, 0, 150))
        p.setPen(Qt.NoPen)
        p.drawRect(self.rect())
        p.setPen(QColor(255, 255, 255))
        p.setFont(QFont("Arial", 24, QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, "TEST 6\nTool + Translucent")

class Test7_FullOverlay(QWidget):
    """Test 7: Full-screen overlay with crosshairs (exactly what the plugin does)"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        else:
            self.setGeometry(0, 0, 1920, 1080)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Big red X across the whole screen
        pen = QPen(QColor(255, 0, 0, 200))
        pen.setWidth(5)
        p.setPen(pen)
        r = self.rect()
        p.drawLine(r.topLeft(), r.bottomRight())
        p.drawLine(r.topRight(), r.bottomLeft())
        # Text in center
        p.setPen(QColor(255, 255, 0))
        p.setFont(QFont("Arial", 48, QFont.Bold))
        p.drawText(r, Qt.AlignCenter, "TEST 7 - FULL OVERLAY")


def run_tests():
    app = QApplication(sys.argv)
    
    tests = [
        ("Test 1: Plain opaque red window", Test1_OpaqueWindow),
        ("Test 2: Semi-transparent (setWindowOpacity)", Test2_SemiTransparentWindow),
        ("Test 3: Frameless + StaysOnTop (opaque)", Test3_FramelessOpaque),
        ("Test 4: Frameless + StaysOnTop + semi-transparent", Test4_FramelessSemiTransparent),
        ("Test 5: WA_TranslucentBackground with paint", Test5_TranslucentBackground),
        ("Test 6: Tool + Translucent", Test6_ToolWindow),
        ("Test 7: Full-screen overlay (plugin replica)", Test7_FullOverlay),
    ]
    
    results = []
    current_test = [0]
    current_window = [None]
    
    def next_test():
        # Close previous
        if current_window[0] is not None:
            current_window[0].close()
            current_window[0] = None
        
        idx = current_test[0]
        if idx >= len(tests):
            # All done
            print("\n=== DIAGNOSTIC COMPLETE ===")
            print("Please report which test numbers you could SEE.")
            print("(e.g. 'I saw tests 1, 2, 3, 4 but NOT 5, 6, 7')")
            app.quit()
            return
        
        name, cls = tests[idx]
        print(f"\n>>> Showing {name} for 4 seconds...")
        window = cls()
        window.show()
        window.raise_()
        current_window[0] = window
        current_test[0] = idx + 1
        QTimer.singleShot(4000, next_test)
    
    print("=== OVERLAY DIAGNOSTIC ===")
    print("7 test windows will appear, each for 4 seconds.")
    print("Watch carefully and note which ones you can SEE.\n")
    
    QTimer.singleShot(500, next_test)
    app.exec_()


if __name__ == "__main__":
    run_tests()
