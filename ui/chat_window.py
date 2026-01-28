# ui/chat_window.py
import sys
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QSystemTrayIcon, QMenu, QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QAction
from ai_engine import AIEngine


class Communicate(QObject):
    """用于线程间通信"""
    update_chat = pyqtSignal(str, str)  # sender, text


class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ai = AIEngine()
        self.comm = Communicate()
        self.comm.update_chat.connect(self.append_message)

        self.init_ui()
        self.setup_tray()

    def init_ui(self):
        self.setWindowTitle("小智 - AI桌面助手")
        self.setWindowIcon(QIcon("resources/icon.ico"))
        self.resize(450, 600)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        self.setStyleSheet("background-color: #f0f0f0;")

        # 标题栏（用于拖动）
        title_label = QLabel("💬 小智助手 (双击托盘呼出)")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("background-color: #4A90E2; color: white; padding: 8px; font-weight: bold;")

        # 聊天区
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;       /* 白色背景 */
                color: #000000;                  /* 黑色文字，确保可见 */
                border: none;
                padding: 10px;
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 14px;
            }
        """)

        # 输入区
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("输入文字消息... (回车发送)")
        self.input_box.setStyleSheet("""
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #ced4da;
                border-radius: 8px;
                font-size: 14px;
                background-color: #ffffff;
                color: #212529;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
                box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
            }
            QLineEdit::placeholder {
                color: #adb5bd;
                opacity: 1;
            }
        """)
        self.input_box.returnPressed.connect(self.send_text_message)

        send_text_btn = QPushButton("发送文字")
        send_text_btn = QPushButton("发送文字")
        send_text_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;      /* 蓝色背景 */
                color: white;                   /* 白色文字 */
                border: none;
                border-radius: 6px;             /* 圆角 */
                padding: 8px 16px;              /* 内边距：上下8px，左右16px */
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;      /* 悬停时变深蓝 */
            }
            QPushButton:pressed {
                background-color: #2C66A8;      /* 按下时更深 */
                padding-top: 9px;               /* 微微下沉效果 */
                padding-bottom: 7px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        send_text_btn.clicked.connect(self.send_text_message)

        voice_btn = QPushButton("🎤 语音对话")
        voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;      /* 绿色：表示“开始” */
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219653;
            }
            QPushButton:pressed {
                background-color: #1E8449;
                padding-top: 9px;
                padding-bottom: 7px;
            }
        """)
        voice_btn.clicked.connect(self.start_voice_conversation)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)
        input_layout.addWidget(send_text_btn)
        input_layout.addWidget(voice_btn)

        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(self.chat_display)
        layout.addLayout(input_layout)
        self.setLayout(layout)

    def send_text_message(self):
        user_text = self.input_box.text().strip()
        if not user_text:
            return
        self.input_box.clear()
        self.append_message("你", user_text)

        # 后台线程处理 AI 回复（避免卡 UI）
        threading.Thread(target=self._get_text_response, args=(user_text,), daemon=True).start()

    def _get_text_response(self, user_text):
        response = self.ai.generate_response(user_text)
        self.comm.update_chat.emit("小智", response)

    def start_voice_conversation(self):
        self.append_message("系统", "请点击右方向键开始说话...")
        threading.Thread(target=self._run_voice_flow, daemon=True).start()

    def _run_voice_flow(self):
        response = self.ai.generate_response_with_voice()
        self.comm.update_chat.emit("小智", f"[语音回复] {response}")

    def append_message(self, sender, text):
        color = "#2C3E50" if sender == "你" else "#2980B9"
        formatted = f'<div style="margin: 8px 0;"><b style="color:{color};">{sender}:</b> {text}</div>'
        self.chat_display.append(formatted)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    # ===== 托盘相关 =====
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon("resources/icon.ico")
        self.tray_icon.setIcon(icon)
        self.tray_icon.activated.connect(self.on_tray_click)

        menu = QMenu()
        show_action = QAction("打开", self)
        quit_action = QAction("退出", self)
        show_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(show_action)
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("小智", "已最小化到托盘", QSystemTrayIcon.MessageIcon.Information, 2000)

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()