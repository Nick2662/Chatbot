# main.py
import sys
from PyQt6.QtWidgets import QApplication
from ui.chat_window import ChatWindow

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = ChatWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()