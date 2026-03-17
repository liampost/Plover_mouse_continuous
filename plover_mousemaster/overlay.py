from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
import sys

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        self.grid_visible = False
        self.grid_rect = QRect()
        self.hints = [] # List of (x, y, label)
        
        # Geometry will be set to full screen
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.geometry())

    def show_grid(self, rect):
        self.grid_rect = rect
        self.grid_visible = True
        self.show()
        self.update()

    def hide_grid(self):
        self.grid_visible = False
        self.hide()

    def set_hints(self, hints):
        self.hints = hints
        self.show()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.grid_visible:
            self.draw_grid(painter)
            
        if self.hints:
            self.draw_hints(painter)

    def draw_grid(self, painter):
        pen = QPen(QColor(255, 0, 0, 150)) # Red semi-transparent
        pen.setWidth(2)
        painter.setPen(pen)
        
        r = self.grid_rect
        # Draw the crosshair for the current rect
        painter.drawLine(r.left(), r.center().y(), r.right(), r.center().y())
        painter.drawLine(r.center().x(), r.top(), r.center().x(), r.bottom())
        
        # Draw the bounding box
        painter.drawRect(r)

    def draw_hints(self, painter):
        font = QFont("Arial", 14, QFont.Bold)
        painter.setFont(font)
        
        for x, y, label in self.hints:
            # Draw a small box with label
            text_rect = painter.fontMetrics().boundingRect(label)
            text_rect.moveCenter(QRect(x, y, 1, 1).center())
            text_rect.adjust(-5, -5, 5, 5)
            
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.setPen(Qt.NoPen)
            painter.drawRect(text_rect)
            
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(text_rect, Qt.AlignCenter, label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OverlayWindow()
    screen_rect = app.primaryScreen().geometry()
    window.show_grid(screen_rect)
    sys.exit(app.exec_())
