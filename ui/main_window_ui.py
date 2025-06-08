#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Layout principal da interface do chat fofo
Design inspirado no Facebook Messenger com cores pastéis
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QLabel, QLineEdit, QPushButton, QFrame, QListWidget,
    QListWidgetItem, QTextEdit, QGraphicsDropShadowEffect, QStackedWidget
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter


class ContactItemWidget(QWidget):
    """Widget personalizado para item de contato na lista"""

    clicked = pyqtSignal(str)  # Emite contact_id quando clicado

    def __init__(self, contact_data: dict):
        super().__init__()
        self.contact_data = contact_data
        self.contact_id = contact_data['contact_id']
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(75)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Layout principal
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(12)

        # Avatar circular
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(50, 50)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Cor do avatar baseada no nome
        avatar_color = self._get_avatar_color(self.contact_data['contact_name'])
        initial = self.contact_data['contact_name'][0].upper() if self.contact_data['contact_name'] else '?'

        self.avatar_label.setStyleSheet(f"""
            QLabel {{
                background-color: {avatar_color};
                color: white;
                border-radius: 25px;
                font-weight: bold;
                font-size: 18px;
                font-family: 'Segoe UI', sans-serif;
            }}
        """)
        self.avatar_label.setText(initial)

        # Informações do contato
        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        # Nome do contato
        name_label = QLabel(self.contact_data['contact_name'])
        name_label.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #2c3e50; margin: 0;")

        # Última mensagem
        last_msg = self.contact_data['last_message']
        if len(last_msg) > 40:
            last_msg = last_msg[:37] + "..."

        # Adicionar indicador se foi enviada por mim
        if self.contact_data['last_message_from_me']:
            last_msg = f"Você: {last_msg}"

        last_msg_label = QLabel(last_msg)
        last_msg_label.setFont(QFont('Segoe UI', 9))
        last_msg_label.setStyleSheet("color: #7f8c8d; margin: 0;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(last_msg_label)

        # Hora da última mensagem
        time_layout = QVBoxLayout()
        time_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        # Formatar hora
        if self.contact_data['last_message_time']:
            from datetime import datetime
            try:
                dt = datetime.fromtimestamp(self.contact_data['last_message_time'])
                time_str = dt.strftime('%H:%M')
            except:
                time_str = ''
        else:
            time_str = ''

        time_label = QLabel(time_str)
        time_label.setFont(QFont('Segoe UI', 8))
        time_label.setStyleSheet("color: #95a5a6; margin: 0;")

        time_layout.addWidget(time_label)

        # Montar layout
        layout.addWidget(self.avatar_label)
        layout.addLayout(info_layout, 1)
        layout.addLayout(time_layout)

        self.setLayout(layout)

        # Estilo do widget
        self.setStyleSheet("""
            ContactItemWidget {
                background-color: #ffffff;
                border-radius: 12px;
                margin: 2px;
            }
            ContactItemWidget:hover {
                background-color: #f8f9fa;
            }
        """)

        # Sombra suave
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def _get_avatar_color(self, name: str) -> str:
        """Retorna cor pastel baseada no nome"""
        colors = [
            "#ff9a9e",  # Rosa pastel
            "#a8e6cf",  # Verde menta
            "#88d8c0",  # Turquesa suave
            "#ffd93d",  # Amarelo suave
            "#6c5ce7",  # Roxo pastel
            "#fd79a8",  # Rosa vibrante suave
            "#81ecec",  # Azul claro
            "#fab1a0",  # Pêssego
            "#e17055",  # Coral suave
            "#00b894"  # Verde oceano
        ]

        # Hash do nome para escolher cor consistente
        hash_val = sum(ord(c) for c in (name or 'default'))
        return colors[hash_val % len(colors)]

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.contact_id)


class MainWindowUI:
    """Layout e estilo da janela principal"""

    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.setup_window()
        self.setup_layout()
        self.apply_styles()

    def setup_window(self):
        """Configurações básicas da janela"""
        self.main_window.setWindowTitle("💬 WhatsApp Chat Interface")
        self.main_window.setGeometry(200, 200, 1200, 800)
        self.main_window.setMinimumSize(900, 600)

    def setup_layout(self):
        """Cria o layout principal"""
        # Widget central
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)

        # Layout principal horizontal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter para redimensionar painéis
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # === PAINEL ESQUERDO (Lista de contatos) ===
        self.setup_contacts_panel(splitter)

        # === PAINEL DIREITO (Chat) ===
        self.setup_chat_panel(splitter)

        # Configurar proporções do splitter
        splitter.setSizes([350, 850])

        main_layout.addWidget(splitter)

    def setup_contacts_panel(self, parent):
        """Configura o painel de contatos"""
        contacts_frame = QFrame()
        contacts_frame.setMinimumWidth(300)
        contacts_frame.setMaximumWidth(400)

        layout = QVBoxLayout(contacts_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === CABEÇALHO DOS CONTATOS ===
        header_frame = QFrame()
        header_frame.setFixedHeight(70)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
            }
        """)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Título
        title_label = QLabel("💬 Conversas")
        title_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")

        # Status de conexão
        self.connection_status = QLabel("🔴 Desconectado")
        self.connection_status.setFont(QFont('Segoe UI', 9))
        self.connection_status.setStyleSheet("color: #ecf0f1;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.connection_status)

        # === BARRA DE BUSCA ===
        search_frame = QFrame()
        search_frame.setFixedHeight(60)
        search_frame.setStyleSheet("background-color: #f8f9fa; border: none;")

        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(15, 10, 15, 10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar conversas...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 13px;
                color: #495057;
            }
            QLineEdit:focus {
                border-color: #667eea;
                outline: none;
            }
        """)

        search_layout.addWidget(self.search_input)

        # === LISTA DE CONTATOS ===
        self.contacts_list = QListWidget()
        self.contacts_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: none;
                outline: none;
                padding: 10px;
            }
            QListWidget::item {
                border: none;
                padding: 5px;
                margin-bottom: 5px;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
        """)

        # Montar painel de contatos
        layout.addWidget(header_frame)
        layout.addWidget(search_frame)
        layout.addWidget(self.contacts_list)

        parent.addWidget(contacts_frame)

    def setup_chat_panel(self, parent):
        """Configura o painel do chat"""
        chat_frame = QFrame()
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Stack widget para alternar entre tela inicial e chat
        self.chat_stack = QStackedWidget()

        # === TELA INICIAL (Bem-vindo) ===
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_icon = QLabel("💬")
        welcome_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_icon.setStyleSheet("font-size: 64px; margin-bottom: 20px;")

        welcome_title = QLabel("Bem-vindo ao Chat!")
        welcome_title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_title.setStyleSheet("color: #667eea; margin-bottom: 10px;")

        welcome_subtitle = QLabel("Selecione uma conversa para começar")
        welcome_subtitle.setFont(QFont('Segoe UI', 12))
        welcome_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_subtitle.setStyleSheet("color: #74b9ff;")

        welcome_layout.addWidget(welcome_icon)
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_subtitle)

        self.chat_stack.addWidget(welcome_widget)

        # === TELA DO CHAT ===
        self.setup_chat_screen()

        chat_layout.addWidget(self.chat_stack)
        parent.addWidget(chat_frame)

    def setup_chat_screen(self):
        """Configura a tela do chat ativo"""
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # === CABEÇALHO DO CHAT ===
        self.chat_header = QFrame()
        self.chat_header.setFixedHeight(70)
        self.chat_header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border: none;
            }
        """)

        header_layout = QHBoxLayout(self.chat_header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Avatar do contato ativo
        self.active_avatar = QLabel()
        self.active_avatar.setFixedSize(45, 45)
        self.active_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_avatar.setStyleSheet("""
            QLabel {
                background-color: #ffffff;
                color: #667eea;
                border-radius: 22px;
                font-weight: bold;
                font-size: 16px;
            }
        """)

        # Informações do contato
        contact_info_layout = QVBoxLayout()
        contact_info_layout.setSpacing(2)

        self.active_contact_name = QLabel("")
        self.active_contact_name.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        self.active_contact_name.setStyleSheet("color: white; margin: 0;")

        self.active_contact_status = QLabel("Online")
        self.active_contact_status.setFont(QFont('Segoe UI', 9))
        self.active_contact_status.setStyleSheet("color: #ecf0f1; margin: 0;")

        contact_info_layout.addWidget(self.active_contact_name)
        contact_info_layout.addWidget(self.active_contact_status)

        # Botões do cabeçalho
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(35, 35)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 17px;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.refresh_btn.setToolTip("Atualizar mensagens")

        header_layout.addWidget(self.active_avatar)
        header_layout.addLayout(contact_info_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)

        # === ÁREA DE MENSAGENS ===
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.messages_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f1f3f4;
            }
            QScrollBar:vertical {
                background: #e9ecef;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #ced4da;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #adb5bd;
            }
        """)

        # Widget que conterá as mensagens
        self.messages_widget = QWidget()
        self.messages_widget.setStyleSheet("background-color: transparent;")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()  # Para empurrar mensagens para baixo

        self.messages_scroll.setWidget(self.messages_widget)

        # === ÁREA DE ENTRADA (Desabilitada por enquanto) ===
        input_frame = QFrame()
        input_frame.setFixedHeight(70)
        input_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #e9ecef;
            }
        """)

        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 10, 20, 10)
        input_layout.setSpacing(10)

        # Campo de texto (desabilitado)
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("📝 Digite uma mensagem... (Em breve!)")
        self.message_input.setEnabled(False)  # TODO: Implementar envio
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 13px;
                color: #6c757d;
            }
            QLineEdit:disabled {
                background-color: #f8f9fa;
                color: #adb5bd;
            }
        """)

        # Botão de anexo (desabilitado)
        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(40, 40)
        attach_btn.setEnabled(False)  # TODO: Implementar anexos
        attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                color: #adb5bd;
            }
        """)

        # Botão de envio (desabilitado)
        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setEnabled(False)  # TODO: Implementar envio
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                color: #adb5bd;
            }
        """)

        input_layout.addWidget(attach_btn)
        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_btn)

        # Montar tela do chat
        chat_layout.addWidget(self.chat_header)
        chat_layout.addWidget(self.messages_scroll, 1)
        chat_layout.addWidget(input_frame)

        self.chat_stack.addWidget(chat_widget)

    def apply_styles(self):
        """Aplica estilos globais"""
        self.main_window.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QSplitter::handle {
                background-color: #dee2e6;
                width: 1px;
            }
            QSplitter::handle:hover {
                background-color: #adb5bd;
            }
        """)

    def show_welcome_screen(self):
        """Mostra a tela de boas-vindas"""
        self.chat_stack.setCurrentIndex(0)

    def show_chat_screen(self):
        """Mostra a tela do chat"""
        self.chat_stack.setCurrentIndex(1)

    def update_connection_status(self, connected: bool):
        """Atualiza o status de conexão"""
        if connected:
            self.connection_status.setText("🟢 Conectado")
            self.connection_status.setStyleSheet("color: #2ecc71;")
        else:
            self.connection_status.setText("🔴 Desconectado")
            self.connection_status.setStyleSheet("color: #e74c3c;")

    def update_active_contact(self, contact_data: dict):
        """Atualiza informações do contato ativo no cabeçalho"""
        name = contact_data['contact_name']
        self.active_contact_name.setText(name)

        # Avatar
        initial = name[0].upper() if name else '?'
        self.active_avatar.setText(initial)

        # Status
        total_msgs = contact_data.get('total_messages', 0)
        self.active_contact_status.setText(f"{total_msgs} mensagens")

    def clear_messages(self):
        """Limpa todas as mensagens da área de chat"""
        # Remove todos os widgets exceto o stretch
        while self.messages_layout.count() > 1:
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def scroll_to_bottom(self):
        """Rola para o final das mensagens"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_contact_to_list(self, contact_data: dict):
        """Adiciona um contato à lista"""
        item = QListWidgetItem()
        contact_widget = ContactItemWidget(contact_data)

        item.setSizeHint(contact_widget.sizeHint())
        self.contacts_list.addItem(item)
        self.contacts_list.setItemWidget(item, contact_widget)

        return contact_widget

    def clear_contacts_list(self):
        """Limpa a lista de contatos"""
        self.contacts_list.clear()