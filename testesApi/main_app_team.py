import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ChatItem(QWidget):
    """Custom widget for chat list items"""

    def __init__(self, icon_path, title, subtitle, time, bold_subtitle=False, disabled=False):
        super().__init__()
        self.setFixedHeight(56)
        self._setup_ui(icon_path, title, subtitle, time, bold_subtitle, disabled)

    def _setup_ui(self, icon_path, title, subtitle, time, bold_subtitle, disabled):
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Icon
        icon_label = QLabel()
        try:
            pixmap = QPixmap(icon_path).scaled(32, 32,
                                               Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        except:
            # Fallback if icon fails to load
            icon_label.setText("T")
            icon_label.setStyleSheet("background-color: #6264a7; color: white; border-radius: 16px;")
        icon_label.setFixedSize(32, 32)
        layout.addWidget(icon_label)

        # Text content
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-weight: 600; 
            font-size: 13px; 
            color: #201f1e;
        """)
        title_label.setToolTip(title)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        title_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_layout.addWidget(title_label)

        # Subtitle
        subtitle_style = f"""
            font-size: 11px; 
            color: {'#605e5c' if not disabled else '#8a8886'}; 
            font-weight: {'bold' if bold_subtitle else 'normal'};
        """
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(subtitle_style)
        subtitle_label.setToolTip(subtitle)
        subtitle_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        subtitle_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_layout.addWidget(subtitle_label)

        layout.addLayout(text_layout)

        # Time
        time_label = QLabel(time)
        time_label.setStyleSheet(f"""
            font-size: 11px; 
            color: {'#605e5c' if not disabled else '#8a8886'};
        """)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        time_label.setFixedWidth(40)
        layout.addWidget(time_label)

        self.setLayout(layout)
        if disabled:
            self.setDisabled(True)


class MessageBubble(QLabel):
    """Custom widget for chat message bubbles"""

    def __init__(self, text, is_sender=False, rounded_top_right=True, rounded_bottom_left=True):
        super().__init__(text)
        self.is_sender = is_sender
        self.rounded_top_right = rounded_top_right
        self.rounded_bottom_left = rounded_bottom_left
        self._setup_ui()

    def _setup_ui(self):
        self.setWordWrap(True)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setContentsMargins(8, 6, 8, 6)
        self.setMaximumWidth(280)
        self._update_style()

    def _update_style(self):
        if self.is_sender:
            bg_color = "#4f2eaa"
            text_color = "white"
            border_radius = "12px 12px 12px 3px" if self.rounded_bottom_left else "12px 12px 3px 3px"
        else:
            bg_color = "#dbe5ff"
            text_color = "#201f1e"
            border_radius = "12px 12px 3px 12px" if self.rounded_top_right else "12px 12px 3px 3px"

        self.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            border-radius: {border_radius};
            font-size: 12px;
            padding: 6px 8px;
        """)


class ChatWindow(QWidget):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()

    def _setup_window(self):
        self.setWindowTitle("Teams Chat Replica")
        self.resize(1200, 720)
        self.setStyleSheet("""
            background-color: #f3f2f1; 
            font-family: Arial, sans-serif;
        """)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_sidebar(main_layout)
        self._create_chat_list(main_layout)
        self._create_chat_area(main_layout)

    def _create_sidebar(self, main_layout):
        sidebar = QVBoxLayout()
        sidebar.setContentsMargins(0, 0, 0, 0)
        sidebar.setSpacing(0)

        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(56)
        sidebar_widget.setStyleSheet("""
            background-color: white; 
            border-right: 1px solid #edebe9;
        """)
        sidebar_widget.setLayout(sidebar)

        # Sidebar buttons
        icons = [
            ("T", True),  # Teams icon, colored
            ("C", False),  # Chat
            ("V", False),  # Video
            ("U", False),  # Users
            ("D", False),  # Calendar
            ("B", False),  # Bell
            ("A", False),  # App
        ]

        for icon_text, active in icons:
            btn = QPushButton(icon_text)
            btn.setFixedSize(56, 56)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                color: {'#6264a7' if active else '#605e5c'}; 
                background-color: transparent; 
                border: none;
                font-size: 16px;
            """)
            sidebar.addWidget(btn)

        sidebar.addStretch()
        main_layout.addWidget(sidebar_widget)

    def _create_chat_list(self, main_layout):
        middle_layout = QVBoxLayout()
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)

        middle_widget = QWidget()
        middle_widget.setFixedWidth(320)
        middle_widget.setLayout(middle_layout)
        middle_widget.setStyleSheet("""
            background-color: #f3f2f1; 
            border-right: 1px solid #edebe9;
        """)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(8, 4, 8, 4)
        search_layout.setSpacing(4)

        back_btn = QPushButton("←")
        back_btn.setFixedSize(24, 24)
        back_btn.setStyleSheet("""
            color: #605e5c; 
            background-color: transparent; 
            border: none; 
            font-size: 16px;
        """)
        search_layout.addWidget(back_btn)

        search_input = QLineEdit()
        search_input.setPlaceholderText("Pesquisar")
        search_input.setStyleSheet("""
            border: 1px solid #edebe9;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 13px;
            background-color: white;
            color: #323130;
        """)
        search_layout.addWidget(search_input)
        middle_layout.addLayout(search_layout)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(8)

        chat_label = QLabel("Chat")
        chat_label.setStyleSheet("""
            font-weight: 700; 
            font-size: 14px; 
            color: #201f1e;
        """)
        header_layout.addWidget(chat_label)
        header_layout.addStretch()

        for icon_char in ["✎", "⚲", "⟳"]:
            btn = QPushButton(icon_char)
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("""
                color: #605e5c; 
                background-color: transparent; 
                border: none; 
                font-size: 14px;
            """)
            header_layout.addWidget(btn)

        middle_layout.addLayout(header_layout)

        # Chat list area
        self._create_chat_list_area(middle_layout)

        # Invite button
        invite_btn = QPushButton("＋ Convidar para o Teams")
        invite_btn.setFixedHeight(40)
        invite_btn.setStyleSheet("""
            background-color: white;
            border-top: 1px solid #edebe9;
            color: #605e5c;
            font-size: 13px;
            font-weight: 600;
            text-align: center;
        """)
        middle_layout.addWidget(invite_btn)

        main_layout.addWidget(middle_widget)

    def _create_chat_list_area(self, middle_layout):
        chat_list_area = QScrollArea()
        chat_list_area.setWidgetResizable(True)
        chat_list_area.setStyleSheet("border: none;")

        chat_list_content = QWidget()
        chat_list_layout = QVBoxLayout()
        chat_list_layout.setContentsMargins(0, 0, 0, 0)
        chat_list_layout.setSpacing(0)
        chat_list_content.setLayout(chat_list_layout)

        # Fixed chats section
        self._add_chat_section(chat_list_layout, "Fixado", self._get_fixed_chats())

        # Recent chats section
        self._add_chat_section(chat_list_layout, "Recentes", self._get_recent_chats(), add_top_margin=True)

        chat_list_layout.addStretch()
        chat_list_area.setWidget(chat_list_content)
        middle_layout.addWidget(chat_list_area)

    def _add_chat_section(self, layout, title, chats, add_top_margin=False):
        """Add a section with title and chat items"""
        label = QLabel(title)
        label.setStyleSheet(f"""
            font-weight: 600; 
            font-size: 13px; 
            color: #201f1e; 
            background-color: #f3f2f1; 
            padding: 6px 12px;
            {'margin-top: 12px;' if add_top_margin else ''}
        """)
        label.setFixedHeight(28)
        layout.addWidget(label)

        for chat_data in chats:
            item = ChatItem(*chat_data)
            layout.addWidget(item)

    def _get_fixed_chats(self):
        """Return fixed chat items data"""
        return [
            ("", "Grupo Fiscal - LR Contabilidade", "Você ⚠️ IN referente os envios das cotas d...", "28/05", False,
             False),
            ("", "Grupo Escritório - LR Contabilidade", "Você se prevevel antes do meio dia", "02/06", False, False),
            ("", "Ney Contador", "ok", "26/05", False, False),
            ("", "Amanda Ellen", "Você: Enviou uma imagem", "16:40", False, True),
        ]

    def _get_recent_chats(self):
        """Return recent chat items data"""
        return [
            ("", "Robson Moura - LR Contabilidade", "do que o ney pediu", "17:07", False, False),
            ("", "Ane LR Contabilidade", "E NÃO APARECE NEM A VERBA", "16:34", True, False),
            ("", "Elaiza Alves", "mas todas a notas são retidas ISS", "15:27", False, False),
            ("", "Adriana Caldeira - LR Contabilidade", "ok", "15:12", False, False),
            ("", "Geferson LR Contabilidade", "obg", "15:12", False, False),
            ("", "Emanuel Fiuza - LR Contabilidade", "Você: emitir certidões da Nutri Valle", "13:52", False, False),
            ("", "Ane LR Contabilidade", "obrigada", "28/05", False, False),
            ("", "Geovanna LR Contadores", "", "05/03", False, False),
        ]

    def _create_chat_area(self, main_layout):
        main_chat_layout = QVBoxLayout()
        main_chat_layout.setContentsMargins(0, 0, 0, 0)
        main_chat_layout.setSpacing(0)

        main_chat_widget = QWidget()
        main_chat_widget.setLayout(main_chat_layout)
        main_chat_widget.setStyleSheet("background-color: white;")

        # Top bar
        self._create_chat_top_bar(main_chat_layout)

        # Messages area
        self._create_messages_area(main_chat_layout)

        # Input area
        self._create_input_area(main_chat_layout)

        main_layout.addWidget(main_chat_widget)

    def _create_chat_top_bar(self, layout):
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 4, 8, 4)
        top_bar.setSpacing(12)

        # Avatar
        avatar_label = QLabel("AC")
        avatar_label.setFixedSize(24, 24)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_label.setStyleSheet("""
            background-color: #f4d6d6; 
            color: #7f1d1d; 
            font-weight: 700; 
            font-size: 9px; 
            border-radius: 12px;
        """)
        top_bar.addWidget(avatar_label)

        # Chat name
        chat_name_label = QLabel("Ane LR Contabilidade")
        chat_name_label.setStyleSheet("""
            font-weight: 700; 
            font-size: 13px; 
            color: #201f1e;
        """)
        top_bar.addWidget(chat_name_label)
        top_bar.addStretch()

        # Tabs
        for tab_name in ["Chat", "Arquivos", "Fotos"]:
            btn = QPushButton(tab_name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                background-color: transparent; 
                border: none; 
                font-size: 13px; 
                color: #605e5c; 
                font-weight: 400;
            """)
            btn.setMinimumWidth(60)
            top_bar.addWidget(btn)

        layout.addLayout(top_bar)

    def _create_messages_area(self, layout):
        messages_area = QScrollArea()
        messages_area.setWidgetResizable(True)
        messages_area.setStyleSheet("border: none;")

        messages_content = QWidget()
        messages_layout = QVBoxLayout()
        messages_layout.setContentsMargins(12, 12, 12, 12)
        messages_layout.setSpacing(16)
        messages_content.setLayout(messages_layout)

        # Add sample messages
        self._add_sample_messages(messages_layout)

        messages_area.setWidget(messages_content)
        layout.addWidget(messages_area)

    def _add_sample_messages(self, layout):
        # Left messages
        self._add_left_message("consegue ver a Marmoraria")
        self._add_left_message("pra mim", with_avatar=False)
        self._add_left_message('', with_avatar=False)
        self._add_left_message("tá aparecendo esse erro agora",
                               with_avatar=False,
                               rounded_top_right=False)

        # Right messages
        self._add_right_message("vou ver")
        self._add_right_message("pc ligou agora")

        # Stacked left messages
        texts = [
            "BOM PREÇO",
            "TAMBÉM DEU DIFERENÇA",
            "SENDO QUE GERÔ FÉRIAS",
            "TUDO",
            "AGORA PRECISO GERAR ESSA RESCISÃO",
            "E NÃO APARECE NEM A VERBA",
        ]

        for i, text in enumerate(texts):
            self._add_left_message(text,
                                   with_avatar=False,
                                   rounded_bottom_left=(i == len(texts) - 1))

    def _add_left_message(self, text, with_avatar=True, rounded_top_right=True, rounded_bottom_left=True):
        container = QHBoxLayout()
        container.setSpacing(8)

        if with_avatar:
            avatar = QLabel("AC")
            avatar.setFixedSize(20, 20)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar.setStyleSheet("""
                background-color: #f4d6d6; 
                color: #7f1d1d; 
                font-weight: 700; 
                font-size: 9px; 
                border-radius: 10px;
                margin-top: 4px;
            """)
            container.addWidget(avatar)
        else:
            container.addSpacing(28)

        bubble = MessageBubble(text,
                               is_sender=False,
                               rounded_top_right=rounded_top_right,
                               rounded_bottom_left=rounded_bottom_left)
        container.addWidget(bubble)
        container.addStretch()

        # Get the parent layout and add this container
        parent_widget = QWidget()
        parent_widget.setLayout(container)
        self.findChild(QVBoxLayout).addWidget(parent_widget)

    def _add_right_message(self, text):
        container = QHBoxLayout()
        container.setSpacing(8)
        container.addStretch()

        bubble = MessageBubble(text, is_sender=True)
        container.addWidget(bubble)

        # Get the parent layout and add this container
        parent_widget = QWidget()
        parent_widget.setLayout(container)
        self.findChild(QVBoxLayout).addWidget(parent_widget)

    def _create_input_area(self, layout):
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(8, 4, 8, 4)
        input_layout.setSpacing(8)

        message_input = QLineEdit()
        message_input.setPlaceholderText("Digite uma mensagem")
        message_input.setStyleSheet("""
            border: 1px solid #edebe9;
            border-radius: 4px;
            padding: 6px 8px;
            font-size: 13px;
            color: #323130;
        """)
        input_layout.addWidget(message_input)

        for icon_char in ["😊", "📎", "+", "✈"]:
            btn = QPushButton(icon_char)
            btn.setFixedSize(28, 28)
            btn.setStyleSheet("""
                background-color: transparent; 
                border: none; 
                font-size: 16px; 
                color: #605e5c;
            """)
            input_layout.addWidget(btn)

        layout.addLayout(input_layout)


def main():
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()