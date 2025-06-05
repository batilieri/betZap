import sys
import time
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QTextEdit, QScrollArea, QFrame, QListWidget,
    QListWidgetItem, QLineEdit, QGraphicsDropShadowEffect, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QLinearGradient, QPalette, QIcon, QPainter, QPainterPath


class ModernContactItem(QFrame):
    def __init__(self, name, phone, last_message="", timestamp="", unread_count=0):
        super().__init__()
        self.name = name
        self.phone = phone
        self.last_message = last_message
        self.timestamp = timestamp
        self.unread_count = unread_count
        self.setup_ui()

    def setup_ui(self):
        self.setMinimumHeight(70)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 8px;
                margin: 4px;
            }
            QFrame:hover {
                background-color: #F5F5F7;
            }
        """)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(42, 42)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {self.get_color(self.name)};
                color: white;
                border-radius: 21px;
                font-weight: bold;
                font-size: 16px;
            }}
        """)
        avatar.setText(self.name[0].upper() if self.name else "?")
        layout.addWidget(avatar)

        # Contact info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        name_layout = QHBoxLayout()
        name_label = QLabel(self.name or self.phone)
        name_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #121212;")
        name_layout.addWidget(name_label)
        name_layout.addStretch()

        time_label = QLabel(self.timestamp)
        time_label.setFont(QFont("Segoe UI", 9))
        time_label.setStyleSheet("color: #7A7A7D;")
        name_layout.addWidget(time_label)
        info_layout.addLayout(name_layout)

        message_layout = QHBoxLayout()
        message_label = QLabel(self.last_message)
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setStyleSheet("color: #7A7A7D;")
        message_label.setMaximumWidth(200)
        message_label.setWordWrap(True)
        message_label.setElideMode(Qt.TextElideMode.ElideRight)
        message_layout.addWidget(message_label)
        message_layout.addStretch()

        if self.unread_count > 0:
            unread_badge = QLabel(str(self.unread_count))
            unread_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            unread_badge.setFixedSize(20, 20)
            unread_badge.setStyleSheet("""
                QLabel {
                    background-color: #25D366;
                    color: white;
                    border-radius: 10px;
                    font-weight: bold;
                    font-size: 10px;
                }
            """)
            message_layout.addWidget(unread_badge)

        info_layout.addLayout(message_layout)
        layout.addLayout(info_layout, 1)

    def get_color(self, name):
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]
        return colors[hash(name or "") % len(colors)]


class ModernMessageBubble(QFrame):
    def __init__(self, text, sender, timestamp, is_from_me=False):
        super().__init__()
        self.text = text
        self.sender = sender
        self.timestamp = timestamp
        self.is_from_me = is_from_me
        self.setup_ui()

    def setup_ui(self):
        self.setMaximumWidth(320)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        if not self.is_from_me:
            sender_label = QLabel(self.sender)
            sender_label.setStyleSheet("color: #25D366; font-weight: bold; font-size: 11px; margin-left: 8px;")
            sender_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(sender_label)

        bubble = QFrame()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)

        message_label = QLabel(self.text)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("color: #333; font-size: 14px; line-height: 1.3;")
        bubble_layout.addWidget(message_label)

        time_label = QLabel(self.timestamp)
        time_label.setStyleSheet("color: #7A7A7D; font-size: 10px; margin-top: 4px;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        bubble_layout.addWidget(time_label)

        if self.is_from_me:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #DCF8C6;
                    border-radius: 12px;
                    border-bottom-right-radius: 4px;
                }
            """)
            # Add shadow for sent messages
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(5)
            shadow.setColor(QColor(0, 0, 0, 15))
            shadow.setOffset(1, 1)
            bubble.setGraphicsEffect(shadow)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border-radius: 12px;
                    border-bottom-left-radius: 4px;
                    border: 1px solid #F0F0F0;
                }
            """)

        layout.addWidget(bubble)
        self.setLayout(layout)


class ModernChatInterface(QMainWindow):
    def __init__(self, webhook_url='https://f87f-186-219-252-19.ngrok-free.app/requisicoes'):
        super().__init__()
        self.webhook_url = webhook_url
        self.current_contact = None
        self.contacts = {
            "Maria": "5561999999999",
            "João": "5561988888888",
            "Pedro": "5561977777777"
        }
        self.setup_ui()
        self.setup_auto_refresh()
        self.apply_styles()

    def setup_ui(self):
        self.setWindowTitle('💬 WhatsApp Modern Interface')
        self.setGeometry(300, 300, 1000, 700)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left panel (contacts)
        left_panel = QFrame()
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        # Search bar
        search_frame = QFrame()
        search_frame.setFixedHeight(40)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(12, 0, 12, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar conversas...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #F5F5F7;
                border: none;
                border-radius: 18px;
                padding: 8px 15px;
                font-size: 13px;
            }
        """)
        search_layout.addWidget(self.search_input)
        left_layout.addWidget(search_frame)

        # Contact list
        self.contact_list = QListWidget()
        self.contact_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
        """)
        self.populate_contact_list()
        self.contact_list.itemClicked.connect(self.select_contact)
        left_layout.addWidget(self.contact_list)

        # Right panel (chat)
        self.chat_stack = QStackedWidget()

        # Welcome screen
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_label = QLabel("💬 Bem-vindo ao WhatsApp Modern\nSelecione uma conversa para começar")
        welcome_label.setFont(QFont("Segoe UI", 14))
        welcome_label.setStyleSheet("color: #7A7A7D; text-align: center;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        self.chat_stack.addWidget(welcome_widget)

        # Chat screen
        self.chat_widget = QWidget()
        chat_layout = QVBoxLayout(self.chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Chat header
        self.chat_header = QFrame()
        self.chat_header.setFixedHeight(70)
        header_layout = QHBoxLayout(self.chat_header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.contact_avatar = QLabel()
        self.contact_avatar.setFixedSize(42, 42)
        self.contact_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contact_avatar.setStyleSheet("""
            QLabel {
                background-color: #4ECDC4;
                color: white;
                border-radius: 21px;
                font-weight: bold;
                font-size: 16px;
            }
        """)
        header_layout.addWidget(self.contact_avatar)

        self.contact_info = QVBoxLayout()
        self.contact_info.setSpacing(4)

        self.contact_name = QLabel("")
        self.contact_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.contact_name.setStyleSheet("color: #121212;")

        self.contact_status = QLabel("online")
        self.contact_status.setFont(QFont("Segoe UI", 10))
        self.contact_status.setStyleSheet("color: #25D366;")

        self.contact_info.addWidget(self.contact_name)
        self.contact_info.addWidget(self.contact_status)
        header_layout.addLayout(self.contact_info, 1)

        # Header buttons
        header_buttons = QHBoxLayout()
        header_buttons.setSpacing(12)

        call_btn = QPushButton()
        call_btn.setFixedSize(36, 36)
        call_btn.setIcon(QIcon.fromTheme("call-start"))
        call_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                border-radius: 18px;
                border: none;
            }
            QPushButton:hover {
                background-color: #E5E5E7;
            }
        """)

        video_btn = QPushButton()
        video_btn.setFixedSize(36, 36)
        video_btn.setIcon(QIcon.fromTheme("camera-web"))
        video_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                border-radius: 18px;
                border: none;
            }
            QPushButton:hover {
                background-color: #E5E5E7;
            }
        """)

        menu_btn = QPushButton()
        menu_btn.setFixedSize(36, 36)
        menu_btn.setIcon(QIcon.fromTheme("application-menu"))
        menu_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                border-radius: 18px;
                border: none;
            }
            QPushButton:hover {
                background-color: #E5E5E7;
            }
        """)

        header_buttons.addWidget(call_btn)
        header_buttons.addWidget(video_btn)
        header_buttons.addWidget(menu_btn)
        header_layout.addLayout(header_buttons)

        chat_layout.addWidget(self.chat_header)

        # Messages area
        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F0F2F5;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #B0B0B0;
            }
        """)

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        self.messages_area.setWidget(self.messages_widget)
        chat_layout.addWidget(self.messages_area, 1)

        # Input area
        input_frame = QFrame()
        input_frame.setFixedHeight(80)
        input_frame.setStyleSheet("background-color: #F0F2F5; border-top: 1px solid #E1E1E1;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 0, 16, 0)

        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(40, 40)
        attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E1E1E1;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #F5F5F7;
            }
        """)
        input_layout.addWidget(attach_btn)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Digite uma mensagem...")
        self.input_text.setFixedHeight(50)
        self.input_text.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #E1E1E1;
                border-radius: 24px;
                padding: 12px 16px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #25D366;
            }
        """)
        input_layout.addWidget(self.input_text, 1)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(50, 50)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                border: none;
                border-radius: 25px;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:disabled {
                background-color: #B0B0B0;
            }
        """)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)

        chat_layout.addWidget(input_frame)
        self.chat_stack.addWidget(self.chat_widget)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(self.chat_stack)
        splitter.setSizes([280, 720])
        main_layout.addWidget(splitter)

    def apply_styles(self):
        # Set application-wide styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F2F5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame {
                background-color: white;
            }
        """)

        # Customize the palette for better color consistency
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 242, 245))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(33, 33, 33))
        self.setPalette(palette)

    def populate_contact_list(self):
        for name, phone in self.contacts.items():
            item = QListWidgetItem()
            contact_item = ModernContactItem(
                name=name,
                phone=phone,
                last_message="Clique para iniciar conversa",
                timestamp=datetime.now().strftime('%H:%M'),
                unread_count=0
            )
            item.setSizeHint(contact_item.sizeHint())
            self.contact_list.addItem(item)
            self.contact_list.setItemWidget(item, contact_item)

    def select_contact(self, item):
        self.chat_stack.setCurrentIndex(1)
        contact_widget = self.contact_list.itemWidget(item)
        if contact_widget:
            self.current_contact = contact_widget.name
            self.contact_name.setText(self.current_contact)
            self.contact_avatar.setText(self.current_contact[0].upper() if self.current_contact else "?")
            self.clear_messages()
            self.load_sample_messages()

    def load_sample_messages(self):
        messages = [
            {"text": "Olá, como você está?", "sender": self.current_contact, "is_from_me": False},
            {"text": "Estou bem, obrigado! E com você?", "sender": "Você", "is_from_me": True},
            {"text": "Tudo ótimo por aqui! O que você está fazendo?", "sender": self.current_contact,
             "is_from_me": False},
            {"text": "Estou trabalhando neste novo projeto de interface. O que acha?", "sender": "Você",
             "is_from_me": True},
            {"text": "Parece incrível! Adorei o design moderno.", "sender": self.current_contact, "is_from_me": False},
        ]

        for msg in messages:
            self.add_message(
                text=msg["text"],
                sender=msg["sender"],
                is_from_me=msg["is_from_me"],
                timestamp=datetime.now().strftime('%H:%M')
            )

        QTimer.singleShot(100, self.scroll_to_bottom)

    def add_message(self, text, sender, timestamp, is_from_me=False):
        message_bubble = ModernMessageBubble(
            text=text,
            sender=sender,
            timestamp=timestamp,
            is_from_me=is_from_me
        )
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_bubble)

        # Add animation
        self.animate_message(message_bubble)

    def animate_message(self, widget):
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        start_rect = widget.geometry()
        start_rect.setHeight(0)

        end_rect = widget.geometry()

        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.start()

    def clear_messages(self):
        while self.messages_layout.count() > 0:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def scroll_to_bottom(self):
        scrollbar = self.messages_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_message(self):
        text = self.input_text.toPlainText().strip()
        if not text or not self.current_contact:
            return

        self.add_message(
            text=text,
            sender="Você",
            is_from_me=True,
            timestamp=datetime.now().strftime('%H:%M')
        )

        # Clear input and scroll to bottom
        self.input_text.clear()
        QTimer.singleShot(100, self.scroll_to_bottom)

        # Simulate reply after delay
        QTimer.singleShot(2000, self.simulate_reply)

    def simulate_reply(self):
        if not self.current_contact:
            return

        replies = [
            "Entendi! Obrigado pela informação.",
            "Isso parece interessante, me conte mais.",
            "Vou verificar isso e te retorno.",
            "Você poderia me enviar mais detalhes?",
            "Perfeito, vamos continuar assim!"
        ]

        reply = replies[int(time.time()) % len(replies)]

        self.add_message(
            text=reply,
            sender=self.current_contact,
            is_from_me=False,
            timestamp=datetime.now().strftime('%H:%M')
        )

        QTimer.singleShot(100, self.scroll_to_bottom)

    def setup_auto_refresh(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.simulate_new_message)
        self.timer.start(10000)  # Check every 10 seconds

    def simulate_new_message(self):
        if not self.current_contact:
            return

        # Only simulate if not in conversation
        if int(time.time()) % 5 != 0:
            return

        messages = [
            "Olá, você está aí?",
            "Tem um momento para conversar?",
            "Enviei aquele documento, já viu?",
            "Podemos marcar uma reunião?",
            "Qual seu horário disponível esta semana?"
        ]

        new_message = messages[int(time.time()) % len(messages)]

        # Add to current conversation if open
        if self.chat_stack.currentIndex() == 1:
            self.add_message(
                text=new_message,
                sender=self.current_contact,
                is_from_me=False,
                timestamp=datetime.now().strftime('%H:%M')
            )
            QTimer.singleShot(100, self.scroll_to_bottom)
        else:
            # Update contact list with new message
            for i in range(self.contact_list.count()):
                item = self.contact_list.item(i)
                widget = self.contact_list.itemWidget(item)
                if widget and widget.name == self.current_contact:
                    new_item = ModernContactItem(
                        name=widget.name,
                        phone=widget.phone,
                        last_message=new_message,
                        timestamp=datetime.now().strftime('%H:%M'),
                        unread_count=widget.unread_count + 1
                    )
                    item.setSizeHint(new_item.sizeHint())
                    self.contact_list.setItemWidget(item, new_item)
                    break


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    window = ModernChatInterface()
    window.show()

    sys.exit(app.exec())