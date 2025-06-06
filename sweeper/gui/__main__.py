from PySide6.QtWidgets import QApplication
import sys
from .mainwindow import MainWindow

def main() -> None:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
