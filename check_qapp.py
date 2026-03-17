import sys
import time

def check_qapp():
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        
        app = QApplication.instance()
        with open(r"C:\Users\postw\Documents\plover_debug2.txt", "w") as f:
            f.write(f"app instance: {app}\n")
            if app:
                f.write(f"thread: {app.thread()}\n")
                f.write(f"top level widgets: {app.topLevelWidgets()}\n")
    except Exception as e:
        with open(r"C:\Users\postw\Documents\plover_debug2.txt", "w") as f:
            f.write(f"Error: {e}\n")

if __name__ == "__main__":
    check_qapp()
