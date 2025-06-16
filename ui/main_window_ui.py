#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Layout principal com design profissional e cores suaves
Paleta moderna e elegante para interface empresarial
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QLabel, QLineEdit, QPushButton, QFrame, QListWidget,
    QListWidgetItem, QTextEdit, QGraphicsDropShadowEffect, QStackedWidget
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter


class ContactItemWidget(QWidget):
    """Widget profissional para item de contato com elevação suave"""

    clicked = pyqtSignal(str)

    def __init__(self, contact_data: dict):
        super().__init__()
        self.contact_data = contact_data
        self.contact_id = contact_data['contact_id']
        self.is_elevated = False
        self.is_selected = False
        self.setup_ui()

    def setup_ui(self):
        self.setFixedHeight(78)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Layout principal
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Avatar circular profissional
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(52, 52)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Cor profissional do avatar
        avatar_color = self._get_professional_avatar_color(self.contact_data['contact_name'])
        initial = self.contact_data['contact_name'][0].upper() if self.contact_data['contact_name'] else '?'

        self.avatar_label.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {avatar_color}, stop:1 {self._darken_color(avatar_color)});
                color: white;
                border-radius: 26px;
                font-weight: 600;
                font-size: 18px;
                font-family: 'Segoe UI', sans-serif;
            }}
        """)
        self.avatar_label.setText(initial)

        # Informações do contato
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Nome do contato
        name_label = QLabel(self.contact_data['contact_name'])
        name_label.setFont(QFont('Segoe UI', 12, QFont.Weight.DemiBold))
        name_label.setStyleSheet("color: #1f2937; margin: 0;")

        # Última mensagem
        last_msg = self.contact_data['last_message']
        if len(last_msg) > 42:
            last_msg = last_msg[:39] + "..."

        if self.contact_data['last_message_from_me']:
            last_msg = f"Você: {last_msg}"

        last_msg_label = QLabel(last_msg)
        last_msg_label.setFont(QFont('Segoe UI', 10))
        last_msg_label.setStyleSheet("color: #6b7280; margin: 0;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(last_msg_label)

        # Informações do lado direito
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        # Hora formatada
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
        time_label.setFont(QFont('Segoe UI', 9))
        time_label.setStyleSheet("color: #9ca3af; margin: 0;")

        # Indicador de mensagens não lidas (se houver)
        unread_count = self.contact_data.get('unread_count', 0)
        if unread_count > 0:
            unread_label = QLabel(str(unread_count))
            unread_label.setFixedSize(20, 20)
            unread_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            unread_label.setStyleSheet("""
                QLabel {
                    background-color: #ef4444;
                    color: white;
                    border-radius: 10px;
                    font-size: 11px;
                    font-weight: 600;
                }
            """)
            right_layout.addWidget(unread_label)

        right_layout.addWidget(time_label)

        # Montar layout
        layout.addWidget(self.avatar_label)
        layout.addLayout(info_layout, 1)
        layout.addLayout(right_layout)

        self.setLayout(layout)

        # Estilo profissional base
        self.setStyleSheet("""
            ContactItemWidget {
                background-color: #ffffff;
                border-radius: 12px;
                margin: 1px;
                border: 1px solid transparent;
            }
            ContactItemWidget:hover {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
            }
        """)

        # Sombra suave profissional
        self._apply_shadow(False)

    def _get_professional_avatar_color(self, name: str) -> str:
        """Retorna cores profissionais e suaves"""
        colors = [
            "#6366f1",  # Indigo moderno
            "#8b5cf6",  # Violeta suave
            "#06b6d4",  # Cyan profissional
            "#10b981",  # Emerald elegante
            "#f59e0b",  # Âmbar corporativo
            "#ef4444",  # Vermelho suave
            "#ec4899",  # Rosa profissional
            "#84cc16",  # Lima corporativo
            "#6b7280",  # Cinza elegante
            "#0ea5e9"  # Azul céu
        ]

        hash_val = sum(ord(c) for c in (name or 'default'))
        return colors[hash_val % len(colors)]

    def _darken_color(self, color: str) -> str:
        """Escurece a cor para criar gradiente"""
        # Mapeamento de cores mais escuras
        color_map = {
            "#6366f1": "#4f46e5",
            "#8b5cf6": "#7c3aed",
            "#06b6d4": "#0891b2",
            "#10b981": "#059669",
            "#f59e0b": "#d97706",
            "#ef4444": "#dc2626",
            "#ec4899": "#db2777",
            "#84cc16": "#65a30d",
            "#6b7280": "#4b5563",
            "#0ea5e9": "#0284c7"
        }
        return color_map.get(color, "#4b5563")

    def _apply_shadow(self, elevated: bool, selected: bool = False):
        """Aplica sombra baseada no estado"""
        shadow = QGraphicsDropShadowEffect()

        if selected:
            # Sombra especial para item selecionado
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(99, 102, 241, 40))  # Cor da marca com transparência
            shadow.setOffset(0, 6)
        elif elevated:
            shadow.setBlurRadius(16)
            shadow.setColor(QColor(0, 0, 0, 25))
            shadow.setOffset(0, 4)
        else:
            shadow.setBlurRadius(8)
            shadow.setColor(QColor(0, 0, 0, 12))
            shadow.setOffset(0, 2)

        self.setGraphicsEffect(shadow)

    def set_selected(self, selected: bool):
        """Define se o item está selecionado com elevação especial"""
        self.is_selected = selected

        if selected:
            # Estilo para item selecionado
            self.setStyleSheet("""
                ContactItemWidget {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #f0f4ff, stop:1 #ffffff);
                    border-radius: 12px;
                    margin: 1px;
                    border: 2px solid #6366f1;
                }
            """)
            self._apply_shadow(False, True)
        else:
            # Voltar ao estilo normal
            self.setStyleSheet("""
                ContactItemWidget {
                    background-color: #ffffff;
                    border-radius: 12px;
                    margin: 1px;
                    border: 1px solid transparent;
                }
                ContactItemWidget:hover {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                }
            """)
            self._apply_shadow(self.is_elevated, False)

    def enterEvent(self, event):
        """Elevação suave ao entrar com mouse"""
        if not self.is_elevated and not self.is_selected:
            self.is_elevated = True
            self._apply_shadow(True, False)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Remove elevação ao sair com mouse"""
        if self.is_elevated and not self.is_selected:
            self.is_elevated = False
            self._apply_shadow(False, False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Efeito de clique com elevação extra"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Elevação extra no clique
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(25)
            shadow.setColor(QColor(99, 102, 241, 50))  # Cor azul com transparência
            shadow.setOffset(0, 8)
            self.setGraphicsEffect(shadow)

            # Emitir sinal de clique
            self.clicked.emit(self.contact_id)

            # Timer para aplicar estado selecionado
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(150, lambda: self.set_selected(True))


class MainWindowUI:
    """Layout principal com design profissional e moderno"""

    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.selected_contact_widget = None  # Rastrear contato selecionado
        self.setup_window()
        self.setup_layout()
        self.apply_professional_styles()

    def setup_window(self):
        """Configurações da janela com tema profissional"""
        self.main_window.setWindowTitle("💬 WhatsApp Business - Interface Profissional")
        self.main_window.setGeometry(200, 200, 1200, 800)
        self.main_window.setMinimumSize(900, 600)

    def setup_layout(self):
        """Layout principal com design corporativo"""
        # Widget central
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter profissional
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e5e7eb;
                width: 1px;
            }
            QSplitter::handle:hover {
                background-color: #d1d5db;
            }
        """)

        # Painel de contatos
        self.setup_professional_contacts_panel(splitter)

        # Painel de chat
        self.setup_professional_chat_panel(splitter)

        # Proporções profissionais
        splitter.setSizes([350, 850])
        main_layout.addWidget(splitter)

    def setup_professional_contacts_panel(self, parent):
        """Painel de contatos com design corporativo"""
        contacts_frame = QFrame()
        contacts_frame.setMinimumWidth(300)
        contacts_frame.setMaximumWidth(400)

        layout = QVBoxLayout(contacts_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabeçalho profissional
        header_frame = QFrame()
        header_frame.setFixedHeight(72)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e293b, stop:1 #334155);
                border: none;
            }
        """)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Título elegante
        title_label = QLabel("💼 Conversas")
        title_label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #f8fafc;")

        # Status de conexão profissional
        self.connection_status = QLabel("🔴 Desconectado")
        self.connection_status.setFont(QFont('Segoe UI', 9, QFont.Weight.Medium))
        self.connection_status.setStyleSheet("color: #cbd5e1;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.connection_status)

        # Barra de busca moderna
        search_frame = QFrame()
        search_frame.setFixedHeight(64)
        search_frame.setStyleSheet("background-color: #f8fafc; border: none;")

        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(16, 12, 16, 12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar conversas...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 10px 16px;
                font-size: 13px;
                color: #1f2937;
                font-weight: 500;
            }
            QLineEdit:focus {
                border-color: #6366f1;
                outline: none;
                background-color: #ffffff;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
        """)

        search_layout.addWidget(self.search_input)

        # Lista de contatos profissional
        self.contacts_list = QListWidget()
        self.contacts_list.setStyleSheet("""
            QListWidget {
                background-color: #f8fafc;
                border: none;
                outline: none;
                padding: 8px;
            }
            QListWidget::item {
                border: none;
                padding: 4px;
                margin-bottom: 2px;
                background-color: transparent;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
        """)

        # Montar painel
        layout.addWidget(header_frame)
        layout.addWidget(search_frame)
        layout.addWidget(self.contacts_list)

        parent.addWidget(contacts_frame)

    def setup_professional_chat_panel(self, parent):
        """Painel de chat com design empresarial"""
        chat_frame = QFrame()
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Stack widget para transições suaves
        self.chat_stack = QStackedWidget()

        # Tela de boas-vindas profissional
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_icon = QLabel("💼")
        welcome_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_icon.setStyleSheet("font-size: 72px; margin-bottom: 24px;")

        welcome_title = QLabel("Bem-vindo ao WhatsApp Business")
        welcome_title.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        welcome_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_title.setStyleSheet("color: #1e293b; margin-bottom: 12px;")

        welcome_subtitle = QLabel("Selecione uma conversa para começar a atender seus clientes")
        welcome_subtitle.setFont(QFont('Segoe UI', 14))
        welcome_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_subtitle.setStyleSheet("color: #64748b;")

        welcome_layout.addWidget(welcome_icon)
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_subtitle)

        self.chat_stack.addWidget(welcome_widget)

        # Tela do chat ativo
        self.setup_professional_chat_screen()

        chat_layout.addWidget(self.chat_stack)
        parent.addWidget(chat_frame)

    def setup_professional_chat_screen(self):
        """Tela de chat com design corporativo"""
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Cabeçalho do chat profissional
        self.chat_header = QFrame()
        self.chat_header.setFixedHeight(72)
        self.chat_header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e293b, stop:1 #334155);
                border: none;
            }
        """)

        header_layout = QHBoxLayout(self.chat_header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Avatar do contato ativo
        self.active_avatar = QLabel()
        self.active_avatar.setFixedSize(48, 48)
        self.active_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_avatar.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #4f46e5);
                color: white;
                border-radius: 24px;
                font-weight: 600;
                font-size: 16px;
            }
        """)

        # Informações do contato
        contact_info_layout = QVBoxLayout()
        contact_info_layout.setSpacing(2)

        self.active_contact_name = QLabel("")
        self.active_contact_name.setFont(QFont('Segoe UI', 15, QFont.Weight.DemiBold))
        self.active_contact_name.setStyleSheet("color: #f8fafc; margin: 0;")

        self.active_contact_status = QLabel("Online")
        self.active_contact_status.setFont(QFont('Segoe UI', 10))
        self.active_contact_status.setStyleSheet("color: #cbd5e1; margin: 0;")

        contact_info_layout.addWidget(self.active_contact_name)
        contact_info_layout.addWidget(self.active_contact_status)

        # Botões do cabeçalho
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(40, 40)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(248, 250, 252, 0.1);
                border: 1px solid rgba(248, 250, 252, 0.2);
                border-radius: 20px;
                color: #f8fafc;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(248, 250, 252, 0.2);
                border-color: rgba(248, 250, 252, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(248, 250, 252, 0.3);
            }
        """)
        self.refresh_btn.setToolTip("Atualizar mensagens")

        header_layout.addWidget(self.active_avatar)
        header_layout.addLayout(contact_info_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)

        # Área de mensagens profissional
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.messages_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f8fafc;
            }
            QScrollBar:vertical {
                background: #f1f5f9;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 4px;
                min-height: 25px;
            }
            QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        # Widget das mensagens
        self.messages_widget = QWidget()
        self.messages_widget.setStyleSheet("background-color: transparent;")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(12, 20, 12, 20)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()

        self.messages_scroll.setWidget(self.messages_widget)

        # Área de entrada profissional
        input_frame = QFrame()
        input_frame.setFixedHeight(76)
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-top: 1px solid #e2e8f0;
            }
        """)

        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(20, 12, 20, 12)
        input_layout.setSpacing(12)

        # Botão de anexo profissional
        self.attach_btn = QPushButton("📎")
        self.attach_btn.setFixedSize(44, 44)
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1, stop:1 #4f46e5);
                border: none;
                border-radius: 22px;
                font-size: 18px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5b21b6, stop:1 #4c1d95);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4c1d95, stop:1 #3730a3);
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        self.attach_btn.setToolTip("Anexar arquivo")

        # Campo de texto profissional
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Digite sua mensagem...")
        self.message_input.setFont(QFont('Segoe UI', 12))
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 22px;
                padding: 12px 18px;
                font-size: 13px;
                color: #1f2937;
            }
            QLineEdit:focus {
                border-color: #6366f1;
                background-color: #ffffff;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
            }
            QLineEdit:disabled {
                background-color: #f1f5f9;
                color: #9ca3af;
                border-color: #e2e8f0;
            }
        """)

        # Botão de envio profissional
        self.send_btn = QPushButton("📤")
        self.send_btn.setFixedSize(44, 44)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #10b981, stop:1 #059669);
                border: none;
                border-radius: 22px;
                font-size: 18px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #047857, stop:1 #065f46);
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #065f46, stop:1 #064e3b);
            }
            QPushButton:disabled {
                background-color: #e5e7eb;
                color: #9ca3af;
            }
        """)
        self.send_btn.setToolTip("Enviar mensagem")

        input_layout.addWidget(self.attach_btn)
        input_layout.addWidget(self.message_input, 1)
        input_layout.addWidget(self.send_btn)

        # Estado inicial dos controles
        self.set_input_enabled(False)

        # Montar tela do chat
        chat_layout.addWidget(self.chat_header)
        chat_layout.addWidget(self.messages_scroll, 1)
        chat_layout.addWidget(input_frame)

        self.chat_stack.addWidget(chat_widget)

    def set_input_enabled(self, enabled: bool):
        """Controla estado dos controles de entrada"""
        self.message_input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        self.attach_btn.setEnabled(enabled)

        if not enabled:
            self.message_input.setPlaceholderText("Selecione um contato para conversar...")
        else:
            self.message_input.setPlaceholderText("Digite sua mensagem...")

    def apply_professional_styles(self):
        """Aplica estilos globais profissionais"""
        self.main_window.setStyleSheet("""
            QMainWindow {
                background-color: #f8fafc;
                font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
            }
        """)

    def show_welcome_screen(self):
        """Mostra tela de boas-vindas"""
        self.chat_stack.setCurrentIndex(0)
        self.set_input_enabled(False)

    def show_chat_screen(self):
        """Mostra tela de chat"""
        self.chat_stack.setCurrentIndex(1)
        self.set_input_enabled(True)

    def update_connection_status(self, connected: bool):
        """Atualiza status de conexão com cores profissionais"""
        if connected:
            self.connection_status.setText("🟢 Conectado")
            self.connection_status.setStyleSheet("color: #10b981; font-weight: 600;")
        else:
            self.connection_status.setText("🔴 Desconectado")
            self.connection_status.setStyleSheet("color: #ef4444; font-weight: 600;")

    def update_active_contact(self, contact_data: dict):
        """Atualiza informações do contato ativo"""
        name = contact_data['contact_name']
        self.active_contact_name.setText(name)

        # Avatar com inicial
        initial = name[0].upper() if name else '?'
        self.active_avatar.setText(initial)

        # Status profissional
        total_msgs = contact_data.get('total_messages', 0)
        if contact_data.get('is_group', False):
            participants = contact_data.get('participants_count', 0)
            status_text = f"Grupo • {participants} participantes • {total_msgs} mensagens"
        else:
            status_text = f"Contato • {total_msgs} mensagens"

        self.active_contact_status.setText(status_text)

    def clear_messages(self):
        """Limpa todas as mensagens"""
        while self.messages_layout.count() > 1:
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def scroll_to_bottom(self):
        """Rola suavemente para o final"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_contact_to_list(self, contact_data: dict):
        """Adiciona contato à lista com widget profissional"""
        item = QListWidgetItem()
        contact_widget = ContactItemWidget(contact_data)

        # Conectar sinal de clique para gerenciar seleção
        contact_widget.clicked.connect(lambda contact_id: self._on_contact_selected(contact_widget))

        item.setSizeHint(contact_widget.sizeHint())
        self.contacts_list.addItem(item)
        self.contacts_list.setItemWidget(item, contact_widget)

        return contact_widget

    def _on_contact_selected(self, selected_widget):
        """Gerencia seleção visual do contato"""
        # Desmarcar contato anterior
        if self.selected_contact_widget and self.selected_contact_widget != selected_widget:
            self.selected_contact_widget.set_selected(False)

        # Marcar novo contato como selecionado
        self.selected_contact_widget = selected_widget
        selected_widget.set_selected(True)

    def clear_contacts_list(self):
        """Limpa lista de contatos"""
        self.selected_contact_widget = None
        self.contacts_list.clear()

    def show_typing_indicator(self, contact_name: str):
        """Indicador de digitação profissional"""
        self.active_contact_status.setText(f"{contact_name} está digitando...")
        self.active_contact_status.setStyleSheet("color: #10b981; font-style: italic; font-weight: 500;")

    def hide_typing_indicator(self, message_count: int):
        """Remove indicador de digitação"""
        self.active_contact_status.setText(f"{message_count} mensagens")
        self.active_contact_status.setStyleSheet("color: #cbd5e1; font-style: normal; font-weight: 400;")

    def show_send_progress(self, progress: int):
        """Mostra progresso de envio"""
        if progress < 100:
            self.send_btn.setText(f"{progress}%")
            self.send_btn.setEnabled(False)
        else:
            self.send_btn.setText("📤")
            self.send_btn.setEnabled(True)

    def show_attachment_progress(self, progress: int):
        """Mostra progresso de anexo"""
        if progress < 100:
            self.attach_btn.setText(f"{progress}%")
            self.attach_btn.setEnabled(False)
        else:
            self.attach_btn.setText("📎")
            self.attach_btn.setEnabled(True)

# =============================================================================
# 🎨 DESIGN PROFISSIONAL E CORPORATIVO IMPLEMENTADO
# =============================================================================
#
# 📊 PALETA DE CORES PROFISSIONAL:
# • Primária: #1e293b (Slate 800) - Cabeçalhos
# • Secundária: #6366f1 (Indigo 500) - Elementos interativos
# • Sucesso: #10b981 (Emerald 500) - Confirmações
# • Aviso: #f59e0b (Amber 500) - Alertas
# • Erro: #ef4444 (Red 500) - Erros
# • Neutros: #f8fafc, #e2e8f0, #94a3b8 - Fundos e bordas
#
# ✨ MELHORIAS DE UX:
# • Elevação suave em contatos (hover + clique)
# • Gradientes profissionais nos avatares
# • Sombras sutis e bem posicionadas
# • Transições suaves nos estados
# • Tipografia corporativa (Segoe UI)
# • Espaçamentos consistentes
#
# 🎯 ELEMENTOS INTERATIVOS:
# • Botões com gradientes e hover effects
# • Campos de entrada com focus states
# • Indicadores de status coloridos
# • Avatares com cores profissionais
# • Scrollbars customizadas
#
# 💼 DESIGN EMPRESARIAL:
# • Cores neutras e profissionais
# • Contrastes adequados para acessibilidade
# • Hierarquia visual clara
# • Elementos bem alinhados
# • Consistência em toda interface
#
# =============================================================================