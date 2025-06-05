#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface WhatsApp com Webhook - Versão Melhorada
Aplicação PyQt6 para receber e exibir mensagens via webhook
- Sem duplicação de contatos
- Conversas individuais separadas
- Mensagens organizadas por remetente/destinatário
"""

import sys
import time
import requests
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QLabel, QScrollArea, QFrame, QListWidget,
    QListWidgetItem, QLineEdit, QGraphicsDropShadowEffect, QStackedWidget,
    QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QPixmap, QIcon


class WebhookListener(QThread):
    """Thread responsável por monitorar o webhook"""

    nova_mensagem = pyqtSignal(dict)
    erro_conexao = pyqtSignal(str)

    def __init__(self, webhook_url):
        super().__init__()
        self.webhook_url = webhook_url
        self.rodando = True
        self.ultimo_total = 0

    def run(self):
        """Loop principal de monitoramento"""
        while self.rodando:
            try:
                self._verificar_novas_mensagens()
            except requests.exceptions.RequestException as e:
                self.erro_conexao.emit(f"Erro de conexão: {str(e)}")
            except Exception as e:
                self.erro_conexao.emit(f"Erro inesperado: {str(e)}")

            time.sleep(2)

    def _verificar_novas_mensagens(self):
        """Verifica se há novas mensagens no servidor"""
        response = requests.get(f"{self.webhook_url}/requisicoes", timeout=5)

        if response.status_code == 200:
            data = response.json()
            total_atual = data.get('total', 0)

            if total_atual > self.ultimo_total:
                requisicoes = data.get('requisicoes', [])
                novas = requisicoes[-(total_atual - self.ultimo_total):]

                for req in novas:
                    mensagem = self._processar_requisicao(req)
                    if mensagem:
                        self.nova_mensagem.emit(mensagem)

                self.ultimo_total = total_atual

    def _processar_requisicao(self, requisicao):
        """Processa uma requisição do webhook"""
        try:
            timestamp = requisicao.get('timestamp', datetime.now().isoformat())
            json_data = requisicao.get('json', {})
            raw_data = requisicao.get('data', '')

            # Tenta processar JSON primeiro
            if json_data:
                return self._extrair_dados_whatsapp(json_data, timestamp)

            # Tenta fazer parse do raw data
            if raw_data:
                try:
                    parsed_data = json.loads(raw_data)
                    return self._extrair_dados_whatsapp(parsed_data, timestamp)
                except json.JSONDecodeError:
                    pass

            return None

        except Exception as e:
            return {
                'chat_id': 'erro',
                'remetente': 'Erro',
                'nome_display': 'Erro no processamento',
                'telefone': '',
                'conteudo': f"Erro: {str(e)}",
                'timestamp': datetime.now().isoformat(),
                'tipo': 'erro',
                'profile_picture': '',
                'from_me': False,
                'is_group': False,
                'message_id': f"erro_{int(time.time())}"
            }

    def _extrair_dados_whatsapp(self, data, timestamp):
        """Extrai dados específicos do formato WhatsApp"""
        if not isinstance(data, dict):
            return None

        # Verifica se é evento do WhatsApp
        event = data.get('event', '')
        if event not in ['webhookDelivery', 'webhookReceived']:
            return None

        try:
            # Dados básicos
            from_me = data.get('fromMe', False)
            is_group = data.get('isGroup', False)
            message_id = data.get('messageId', '')

            # Dados do remetente
            sender = data.get('sender', {})
            sender_name = sender.get('pushName', '')
            sender_id = sender.get('id', '')
            sender_profile = sender.get('profilePicture', '')

            # Dados do chat
            chat = data.get('chat', {})
            chat_id = chat.get('id', '')
            chat_profile = chat.get('profilePicture', '')

            # Conteúdo da mensagem
            msg_content = data.get('msgContent', {})
            conversation = msg_content.get('conversation', 'Mensagem sem conteúdo')

            # Timestamp
            moment = data.get('moment', 0)
            if moment > 0:
                dt = datetime.fromtimestamp(moment)
                timestamp_formatado = dt.isoformat()
            else:
                timestamp_formatado = timestamp

            # Lógica para determinar dados do contato
            if is_group:
                # Para grupos, o chat_id é a chave e sender_name é quem enviou
                contact_key = chat_id
                contact_name = f"Grupo {self._formatar_telefone(chat_id)}"
                contact_phone = self._formatar_telefone(chat_id)
                contact_profile = chat_profile
                remetente_final = sender_name or "Membro do grupo"
            else:
                # Para conversas individuais, sempre usa o chat_id como contato
                contact_key = chat_id

                if from_me:
                    # Mensagem enviada por mim
                    contact_name = sender_name or self._formatar_telefone(chat_id)
                    contact_phone = self._formatar_telefone(chat_id)
                    contact_profile = chat_profile
                    remetente_final = "Você"
                else:
                    # Mensagem recebida
                    contact_name = sender_name or self._formatar_telefone(sender_id)
                    contact_phone = self._formatar_telefone(chat_id)
                    contact_profile = sender_profile or chat_profile
                    remetente_final = sender_name or contact_name

            return {
                'chat_id': contact_key,
                'remetente': remetente_final,
                'nome_display': contact_name,
                'telefone': contact_phone,
                'telefone_raw': contact_key,
                'conteudo': conversation,
                'timestamp': timestamp_formatado,
                'tipo': 'whatsapp',
                'profile_picture': contact_profile,
                'from_me': from_me,
                'is_group': is_group,
                'message_id': message_id,
                'sender_id': sender_id,
                'sender_name': sender_name
            }

        except Exception as e:
            print(f"Erro ao extrair dados WhatsApp: {e}")
            return None

    def _formatar_telefone(self, telefone):
        """Formata número de telefone brasileiro"""
        if not telefone:
            return "Desconhecido"

        numeros = ''.join(filter(str.isdigit, telefone))

        if len(numeros) == 11:  # Celular
            return f"({numeros[:2]}) {numeros[2:7]}-{numeros[7:]}"
        elif len(numeros) == 10:  # Fixo
            return f"({numeros[:2]}) {numeros[2:6]}-{numeros[6:]}"
        elif len(numeros) >= 12 and numeros.startswith('55'):  # Com código do país
            num_br = numeros[2:]
            if len(num_br) == 11:
                return f"({num_br[:2]}) {num_br[2:7]}-{num_br[7:]}"

        return telefone

    def parar(self):
        """Para o monitoramento"""
        self.rodando = False


class ContactItem(QFrame):
    """Widget para exibir um contato na lista"""

    def __init__(self, chat_id, name, phone, last_message="", timestamp="", unread_count=0, profile_picture=""):
        super().__init__()
        self.chat_id = chat_id
        self.name = name
        self.phone = phone
        self.last_message = last_message
        self.timestamp = timestamp
        self.unread_count = unread_count
        self.profile_picture = profile_picture

        self._setup_ui()

        if profile_picture:
            self._carregar_avatar()

    def _setup_ui(self):
        """Configura a interface do item de contato"""
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

        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # Avatar
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(42, 42)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self._get_color()};
                color: white;
                border-radius: 21px;
                font-weight: bold;
                font-size: 16px;
            }}
        """)
        self.avatar_label.setText(self.name[0].upper() if self.name else "?")
        layout.addWidget(self.avatar_label)

        # Informações do contato
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # Nome e horário
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

        # Mensagem e contador
        message_layout = QHBoxLayout()

        display_message = self.last_message
        if len(display_message) > 30:
            display_message = display_message[:30] + "..."

        message_label = QLabel(display_message)
        message_label.setFont(QFont("Segoe UI", 10))
        message_label.setStyleSheet("color: #7A7A7D;")
        message_label.setMaximumWidth(200)
        message_layout.addWidget(message_label)
        message_layout.addStretch()

        # Badge de não lidas
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

    def _carregar_avatar(self):
        """Carrega avatar da URL"""
        try:
            response = requests.get(self.profile_picture, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                if pixmap.loadFromData(response.content):
                    scaled_pixmap = pixmap.scaled(
                        42, 42,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )

                    # Máscara circular
                    mask = QPixmap(42, 42)
                    mask.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(mask)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setBrush(Qt.GlobalColor.black)
                    painter.drawEllipse(0, 0, 42, 42)
                    painter.end()

                    scaled_pixmap.setMask(mask.createMaskFromColor(Qt.GlobalColor.transparent))
                    self.avatar_label.setPixmap(scaled_pixmap)
                    self.avatar_label.setText("")
        except:
            pass

    def _get_color(self):
        """Retorna cor baseada no nome"""
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]
        return colors[hash(self.name or "") % len(colors)]


class MessageBubble(QFrame):
    """Widget para exibir uma mensagem"""

    def __init__(self, text, sender, timestamp, is_from_me=False, message_type="text"):
        super().__init__()
        self.text = text
        self.sender = sender
        self.timestamp = timestamp
        self.is_from_me = is_from_me
        self.message_type = message_type

        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface da mensagem"""
        self.setMaximumWidth(320)
        self.setStyleSheet("background-color: transparent;")  # Fundo transparente

        # Layout principal da mensagem
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 4, 0, 4)

        # Container da mensagem
        message_container = QVBoxLayout()
        message_container.setContentsMargins(0, 0, 0, 0)

        # Nome do remetente (apenas para mensagens recebidas)
        if not self.is_from_me:
            sender_label = QLabel(self.sender)
            sender_label.setStyleSheet("""
                color: #25D366; 
                font-weight: bold; 
                font-size: 11px; 
                margin-left: 8px;
                background-color: transparent;
            """)
            message_container.addWidget(sender_label)

        # Bolha da mensagem
        bubble = QFrame()
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)

        # Ícone baseado no tipo
        icon_text = ""
        if self.message_type == "webhook":
            icon_text = "🔗 "
        elif self.message_type == "erro":
            icon_text = "⚠️ "

        # Texto da mensagem
        message_label = QLabel(icon_text + self.text)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            color: #333; 
            font-size: 14px; 
            line-height: 1.3;
            background-color: transparent;
        """)
        bubble_layout.addWidget(message_label)

        # Horário
        time_str = self._format_time()
        time_label = QLabel(time_str)
        time_label.setStyleSheet("""
            color: #7A7A7D; 
            font-size: 10px; 
            margin-top: 4px;
            background-color: transparent;
        """)

        # Estilo da bolha e alinhamento
        if self.is_from_me:
            # Mensagens enviadas - lado direito, cor verde
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #DCF8C6;
                    border-radius: 12px;
                    border-bottom-right-radius: 4px;
                    border: 1px solid #C8E6C9;
                }
            """)
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

            # Adiciona stretch à esquerda para empurrar para direita
            main_layout.addStretch(1)
            message_container.addWidget(bubble)
            main_layout.addLayout(message_container)

        else:
            # Mensagens recebidas - lado esquerdo
            if self.message_type == "erro":
                bg_color = "#FFEBEE"
                border_color = "#FFCDD2"
            elif self.message_type == "webhook":
                bg_color = "#E3F2FD"
                border_color = "#BBDEFB"
            else:
                bg_color = "#FFFFFF"
                border_color = "#E0E0E0"

            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border-radius: 12px;
                    border-bottom-left-radius: 4px;
                    border: 1px solid {border_color};
                }}
            """)
            time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            # Adiciona stretch à direita para manter na esquerda
            message_container.addWidget(bubble)
            main_layout.addLayout(message_container)
            main_layout.addStretch(1)

        bubble_layout.addWidget(time_label)
        self.setLayout(main_layout)

    def _format_time(self):
        """Formata o horário da mensagem"""
        try:
            if isinstance(self.timestamp, str):
                dt = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
                return dt.strftime('%H:%M')
            return self.timestamp
        except:
            return datetime.now().strftime('%H:%M')


class ChatInterface(QMainWindow):
    """Interface principal do chat"""

    def __init__(self, webhook_url='http://localhost:5000'):
        super().__init__()
        self.webhook_url = webhook_url
        self.current_contact = None
        self.contacts = {}  # {chat_id: {dados_do_contato}}
        self.contact_messages = {}  # {chat_id: [lista_de_mensagens]}
        self.contact_widgets = {}  # {chat_id: widget_na_lista}
        self.webhook_listener = None

        self._setup_ui()
        self._setup_webhook_listener()
        self._apply_styles()

    def _setup_ui(self):
        """Configura a interface principal"""
        self.setWindowTitle('💬 WhatsApp Interface - Webhook')
        self.setGeometry(300, 300, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter para painéis redimensionáveis
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Painel esquerdo (contatos)
        self._setup_left_panel(splitter)

        # Painel direito (chat)
        self._setup_right_panel(splitter)

        splitter.setSizes([280, 720])
        main_layout.addWidget(splitter)

    def _setup_left_panel(self, parent):
        """Configura o painel de contatos"""
        left_panel = QFrame()
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        # Status da conexão
        self.status_label = QLabel("🔴 Desconectado do webhook")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #FFEBEE;
                color: #D32F2F;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        left_layout.addWidget(self.status_label)

        # Barra de busca
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

        # Lista de contatos
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
        self.contact_list.itemClicked.connect(self._select_contact)
        left_layout.addWidget(self.contact_list)

        parent.addWidget(left_panel)

    def _setup_right_panel(self, parent):
        """Configura o painel do chat"""
        self.chat_stack = QStackedWidget()

        # Tela de boas-vindas
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        welcome_label = QLabel(
            "💬 Interface WhatsApp com Webhook\n\n"
            "🔗 Aguardando mensagens...\n\n"
            "As conversas aparecerão automaticamente\n"
            "quando chegarem mensagens pelo webhook."
        )
        welcome_label.setFont(QFont("Segoe UI", 14))
        welcome_label.setStyleSheet("color: #7A7A7D; text-align: center;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)

        self.chat_stack.addWidget(welcome_widget)

        # Tela do chat
        self._setup_chat_screen()

        parent.addWidget(self.chat_stack)

    def _setup_chat_screen(self):
        """Configura a tela do chat"""
        self.chat_widget = QWidget()
        chat_layout = QVBoxLayout(self.chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Cabeçalho do chat
        self._setup_chat_header(chat_layout)

        # Área de mensagens
        self._setup_messages_area(chat_layout)

        # Área de entrada (informativa)
        self._setup_input_area(chat_layout)

        self.chat_stack.addWidget(self.chat_widget)

    def _setup_chat_header(self, parent_layout):
        """Configura o cabeçalho do chat"""
        self.chat_header = QFrame()
        self.chat_header.setFixedHeight(70)
        header_layout = QHBoxLayout(self.chat_header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Avatar do contato
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

        # Informações do contato
        contact_info = QVBoxLayout()
        contact_info.setSpacing(4)

        self.contact_name = QLabel("")
        self.contact_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.contact_name.setStyleSheet("color: #121212;")

        self.contact_status = QLabel("via webhook")
        self.contact_status.setFont(QFont("Segoe UI", 10))
        self.contact_status.setStyleSheet("color: #25D366;")

        contact_info.addWidget(self.contact_name)
        contact_info.addWidget(self.contact_status)
        header_layout.addLayout(contact_info, 1)

        # Botões do cabeçalho
        self._setup_header_buttons(header_layout)

        parent_layout.addWidget(self.chat_header)

    def _setup_header_buttons(self, parent_layout):
        """Configura os botões do cabeçalho"""
        header_buttons = QHBoxLayout()
        header_buttons.setSpacing(12)

        # Botão reconectar
        reconnect_btn = QPushButton("🔄")
        reconnect_btn.setFixedSize(36, 36)
        reconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                border-radius: 18px;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #E5E5E7;
            }
        """)
        reconnect_btn.clicked.connect(self._reconnect_webhook)
        reconnect_btn.setToolTip("Reconectar webhook")

        # Botão limpar
        clear_btn = QPushButton("🗑️")
        clear_btn.setFixedSize(36, 36)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                border-radius: 18px;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #E5E5E7;
            }
        """)
        clear_btn.clicked.connect(self._clear_webhook_messages)
        clear_btn.setToolTip("Limpar mensagens do webhook")

        header_buttons.addWidget(reconnect_btn)
        header_buttons.addWidget(clear_btn)
        parent_layout.addLayout(header_buttons)

    def _setup_messages_area(self, parent_layout):
        """Configura a área de mensagens"""
        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
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
        self.messages_widget.setStyleSheet("background-color: transparent;")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()

        self.messages_area.setWidget(self.messages_widget)
        parent_layout.addWidget(self.messages_area, 1)

    def _setup_input_area(self, parent_layout):
        """Configura a área de entrada (informativa)"""
        input_frame = QFrame()
        input_frame.setFixedHeight(60)
        input_frame.setStyleSheet("background-color: #F0F2F5; border-top: 1px solid #E1E1E1;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 0, 16, 0)

        info_label = QLabel("💡 Mensagens chegam automaticamente via webhook")
        info_label.setStyleSheet("color: #7A7A7D; font-size: 12px; font-style: italic; background-color: transparent;")
        input_layout.addWidget(info_label)

        parent_layout.addWidget(input_frame)

    def _setup_webhook_listener(self):
        """Configura o listener do webhook"""
        try:
            self.webhook_listener = WebhookListener(self.webhook_url)
            self.webhook_listener.nova_mensagem.connect(self._processar_nova_mensagem)
            self.webhook_listener.erro_conexao.connect(self._tratar_erro_webhook)
            self.webhook_listener.start()

            # Testa conexão inicial
            QTimer.singleShot(1000, self._testar_conexao_inicial)

        except Exception as e:
            self.status_label.setText(f"❌ Erro ao conectar: {str(e)}")

    def _testar_conexao_inicial(self):
        """Testa a conexão inicial com o webhook"""
        try:
            response = requests.get(f"{self.webhook_url}/status", timeout=5)
            if response.status_code == 200:
                self._set_status_connected()
            else:
                raise Exception(f"Status {response.status_code}")
        except Exception as e:
            self.status_label.setText(f"🔴 Erro de conexão: {str(e)[:30]}...")

    def _set_status_connected(self):
        """Define status como conectado"""
        self.status_label.setText("🟢 Conectado ao webhook")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #E8F5E8;
                color: #2E7D32;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
        """)

    def _processar_nova_mensagem(self, mensagem_data):
        """Processa nova mensagem recebida"""
        try:
            # Extrai dados da mensagem
            chat_id = mensagem_data.get('chat_id')
            remetente = mensagem_data.get('remetente', 'Desconhecido')
            nome_display = mensagem_data.get('nome_display', remetente)
            telefone = mensagem_data.get('telefone', '')
            conteudo = mensagem_data.get('conteudo', '')
            timestamp = mensagem_data.get('timestamp', datetime.now().isoformat())
            tipo = mensagem_data.get('tipo', 'whatsapp')
            profile_picture = mensagem_data.get('profile_picture', '')
            from_me = mensagem_data.get('from_me', False)
            is_group = mensagem_data.get('is_group', False)
            message_id = mensagem_data.get('message_id', '')

            if not chat_id:
                print("Mensagem sem chat_id, ignorando...")
                return

            # Processa/atualiza contato
            self._processar_contato(chat_id, nome_display, telefone, profile_picture,
                                    is_group, conteudo, timestamp)

            # Adiciona mensagem ao histórico
            nova_mensagem = {
                'text': conteudo,
                'sender': remetente,
                'timestamp': timestamp,
                'is_from_me': from_me,
                'message_type': tipo,
                'message_id': message_id
            }

            if chat_id not in self.contact_messages:
                self.contact_messages[chat_id] = []

            # Evita duplicar mensagens com mesmo ID
            existing_ids = [msg.get('message_id') for msg in self.contact_messages[chat_id]]
            if message_id not in existing_ids:
                self.contact_messages[chat_id].append(nova_mensagem)

                # Se a conversa está aberta, adiciona a mensagem
                if self.current_contact == chat_id:
                    self._add_message(
                        text=conteudo,
                        sender=remetente,
                        timestamp=timestamp,
                        is_from_me=from_me,
                        message_type=tipo
                    )
                    QTimer.singleShot(100, self._scroll_to_bottom)

                # Atualiza widget do contato na lista
                self._atualizar_widget_contato(chat_id, conteudo, timestamp, from_me)

            # Atualiza status
            status_msg = f"🟢 Nova mensagem de {nome_display}"
            if is_group:
                status_msg += " (Grupo)"
            self.status_label.setText(status_msg)
            QTimer.singleShot(3000, lambda: self.status_label.setText("🟢 Conectado ao webhook"))

        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")

    def _processar_contato(self, chat_id, nome_display, telefone, profile_picture,
                           is_group, ultima_mensagem, timestamp):
        """Processa contato (adiciona ou atualiza)"""
        if chat_id not in self.contacts:
            # Novo contato
            self.contacts[chat_id] = {
                'name': nome_display,
                'phone': telefone,
                'profile_picture': profile_picture,
                'is_group': is_group,
                'unread_count': 0
            }
            self.contact_messages[chat_id] = []
            self._adicionar_contato_lista(chat_id, nome_display, telefone,
                                          ultima_mensagem, timestamp, profile_picture)
        else:
            # Contato existente - atualiza apenas dados básicos se necessário
            contact = self.contacts[chat_id]
            if not contact['name'] or contact['name'] == telefone:
                contact['name'] = nome_display
            if not contact['profile_picture']:
                contact['profile_picture'] = profile_picture

    def _adicionar_contato_lista(self, chat_id, nome, telefone, ultima_mensagem,
                                 timestamp, profile_picture=""):
        """Adiciona novo contato à lista"""
        item = QListWidgetItem()
        contact_item = ContactItem(
            chat_id=chat_id,
            name=nome,
            phone=telefone,
            last_message=ultima_mensagem,
            timestamp=self._formatar_timestamp(timestamp),
            unread_count=1 if self.current_contact != chat_id else 0,
            profile_picture=profile_picture
        )
        item.setSizeHint(contact_item.sizeHint())

        # Insere no topo da lista
        self.contact_list.insertItem(0, item)
        self.contact_list.setItemWidget(item, contact_item)
        self.contact_widgets[chat_id] = item

    def _atualizar_widget_contato(self, chat_id, ultima_mensagem, timestamp, from_me):
        """Atualiza widget do contato na lista"""
        if chat_id not in self.contact_widgets:
            return

        item = self.contact_widgets[chat_id]
        old_widget = self.contact_list.itemWidget(item)

        if old_widget:
            contact_data = self.contacts[chat_id]

            # Calcula contador de não lidas
            unread_count = old_widget.unread_count
            if self.current_contact != chat_id and not from_me:
                unread_count += 1
            elif self.current_contact == chat_id:
                unread_count = 0

            # Remove item antigo
            row = self.contact_list.row(item)
            self.contact_list.takeItem(row)

            # Cria novo item atualizado
            new_item = QListWidgetItem()
            new_contact_item = ContactItem(
                chat_id=chat_id,
                name=contact_data['name'],
                phone=contact_data['phone'],
                last_message=ultima_mensagem,
                timestamp=self._formatar_timestamp(timestamp),
                unread_count=unread_count,
                profile_picture=contact_data.get('profile_picture', '')
            )
            new_item.setSizeHint(new_contact_item.sizeHint())

            # Insere no topo da lista
            self.contact_list.insertItem(0, new_item)
            self.contact_list.setItemWidget(new_item, new_contact_item)
            self.contact_widgets[chat_id] = new_item

    def _select_contact(self, item):
        """Seleciona contato e carrega mensagens"""
        contact_widget = self.contact_list.itemWidget(item)

        if contact_widget and contact_widget.chat_id:
            self.chat_stack.setCurrentIndex(1)
            chat_id = contact_widget.chat_id
            self.current_contact = chat_id

            if chat_id in self.contacts:
                contact_data = self.contacts[chat_id]

                # Atualiza header do chat
                self._atualizar_header_chat(contact_data)

                # Limpa mensagens antigas e carrega histórico
                self._clear_messages()
                self._carregar_historico_mensagens(chat_id)

                # Marca como lido
                self._marcar_como_lido(chat_id)

                QTimer.singleShot(100, self._scroll_to_bottom)

    def _atualizar_header_chat(self, contact_data):
        """Atualiza o cabeçalho do chat"""
        self.contact_name.setText(contact_data['name'])

        # Atualiza avatar
        if contact_data.get('profile_picture'):
            self._carregar_avatar_header(contact_data['profile_picture'])
        else:
            self.contact_avatar.setText(contact_data['name'][0].upper() if contact_data['name'] else "?")
            self.contact_avatar.setStyleSheet(f"""
                QLabel {{
                    background-color: {self._get_contact_color(contact_data['name'])};
                    color: white;
                    border-radius: 21px;
                    font-weight: bold;
                    font-size: 16px;
                }}
            """)

        # Atualiza status
        status_text = "via webhook"
        if contact_data.get('is_group'):
            status_text = "Grupo • " + status_text
        self.contact_status.setText(status_text)

    def _carregar_avatar_header(self, profile_picture_url):
        """Carrega avatar do cabeçalho do chat"""
        try:
            response = requests.get(profile_picture_url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                if pixmap.loadFromData(response.content):
                    scaled_pixmap = pixmap.scaled(
                        42, 42,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation
                    )

                    # Máscara circular
                    mask = QPixmap(42, 42)
                    mask.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(mask)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    painter.setBrush(Qt.GlobalColor.black)
                    painter.drawEllipse(0, 0, 42, 42)
                    painter.end()

                    scaled_pixmap.setMask(mask.createMaskFromColor(Qt.GlobalColor.transparent))
                    self.contact_avatar.setPixmap(scaled_pixmap)
                    self.contact_avatar.setText("")
        except:
            pass

    def _carregar_historico_mensagens(self, chat_id):
        """Carrega mensagens do histórico"""
        if chat_id in self.contact_messages:
            for msg in self.contact_messages[chat_id]:
                self._add_message(
                    text=msg['text'],
                    sender=msg['sender'],
                    timestamp=msg['timestamp'],
                    is_from_me=msg['is_from_me'],
                    message_type=msg.get('message_type', 'text')
                )

    def _marcar_como_lido(self, chat_id):
        """Marca conversa como lida"""
        if chat_id in self.contact_widgets:
            item = self.contact_widgets[chat_id]
            old_widget = self.contact_list.itemWidget(item)

            if old_widget:
                contact_data = self.contacts[chat_id]

                # Cria novo widget com contador zerado
                new_contact_item = ContactItem(
                    chat_id=chat_id,
                    name=old_widget.name,
                    phone=old_widget.phone,
                    last_message=old_widget.last_message,
                    timestamp=old_widget.timestamp,
                    unread_count=0,  # Zera contador
                    profile_picture=contact_data.get('profile_picture', '')
                )
                item.setSizeHint(new_contact_item.sizeHint())
                self.contact_list.setItemWidget(item, new_contact_item)

    def _get_contact_color(self, name):
        """Retorna cor baseada no nome do contato"""
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]
        return colors[hash(name or "") % len(colors)]

    def _formatar_timestamp(self, timestamp):
        """Formata timestamp para exibição"""
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp

            now = datetime.now()

            # Se for hoje, mostra apenas a hora
            if dt.date() == now.date():
                return dt.strftime('%H:%M')
            # Se for ontem
            elif (now.date() - dt.date()).days == 1:
                return "Ontem"
            # Se for esta semana
            elif (now.date() - dt.date()).days < 7:
                dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                return dias[dt.weekday()]
            # Senão, mostra a data
            else:
                return dt.strftime('%d/%m')
        except:
            return datetime.now().strftime('%H:%M')

    def _tratar_erro_webhook(self, erro):
        """Trata erros de conexão com webhook"""
        self.status_label.setText(f"🔴 {erro}")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #FFEBEE;
                color: #D32F2F;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
        """)

    def _reconnect_webhook(self):
        """Reconecta ao webhook"""
        if self.webhook_listener:
            self.webhook_listener.parar()
            self.webhook_listener.wait()

        self._setup_webhook_listener()
        self.status_label.setText("🟡 Reconectando...")

    def _clear_webhook_messages(self):
        """Limpa mensagens do servidor webhook"""
        try:
            response = requests.post(f"{self.webhook_url}/limpar", timeout=5)
            if response.status_code == 200:
                QMessageBox.information(self, "Sucesso", "Mensagens do webhook foram limpas!")
                if self.webhook_listener:
                    self.webhook_listener.ultimo_total = 0
            else:
                QMessageBox.warning(self, "Erro", f"Erro ao limpar: {response.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro de conexão: {str(e)}")

    def _apply_styles(self):
        """Aplica estilos globais"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F2F5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame {
                background-color: white;
            }
        """)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 242, 245))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(33, 33, 33))
        self.setPalette(palette)

    def _add_message(self, text, sender, timestamp, is_from_me=False, message_type="text"):
        """Adiciona mensagem à conversa"""
        message_bubble = MessageBubble(
            text=text,
            sender=sender,
            timestamp=timestamp,
            is_from_me=is_from_me,
            message_type=message_type
        )
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, message_bubble)
        self._animate_message(message_bubble)

    def _animate_message(self, widget):
        """Anima entrada da mensagem"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(300)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        start_rect = widget.geometry()
        start_rect.setHeight(0)
        end_rect = widget.geometry()

        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.start()

    def _clear_messages(self):
        """Limpa todas as mensagens da conversa"""
        while self.messages_layout.count() > 1:  # Mantém o stretch
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _scroll_to_bottom(self):
        """Rola para o final da conversa"""
        scrollbar = self.messages_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        if self.webhook_listener:
            self.webhook_listener.parar()
            self.webhook_listener.wait()
        event.accept()


class ConfigWindow(QWidget):
    """Janela de configuração do webhook"""

    def __init__(self):
        super().__init__()
        self.main_window = None
        self._setup_ui()

    def _setup_ui(self):
        """Configura a interface da janela de configuração"""
        self.setWindowTitle('Configuração do Webhook')
        self.setFixedSize(500, 300)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("🔗 Configuração do Webhook")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #25D366; margin: 10px;")
        layout.addWidget(title)

        # Campo URL
        url_label = QLabel("URL do Webhook:")
        url_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://seu-webhook.ngrok.io")
        self.url_input.setText("https://0587-187-36-92-93.ngrok-free.app")
        self.url_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #E1E1E1;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #25D366;
                outline: none;
            }
        """)
        layout.addWidget(self.url_input)

        # Nota informativa
        note = QLabel(
            "💡 Certifique-se de que o webhook está rodando e acessível.\n"
            "A URL será testada antes de conectar."
        )
        note.setStyleSheet("color: #666; font-size: 11px; margin: 5px; padding: 8px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        # Botões
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        test_btn = QPushButton("🧪 Testar Conexão")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                border: 2px solid #E1E1E1;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #E5E5E7;
                border-color: #25D366;
            }
            QPushButton:pressed {
                background-color: #D5D5D7;
            }
        """)
        test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(test_btn)

        save_btn = QPushButton("✅ Conectar")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:pressed {
                background-color: #0F7A6B;
            }
        """)
        save_btn.clicked.connect(self._connect_webhook)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        # Status
        self.status_label = QLabel("Digite a URL do seu webhook e teste a conexão")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 12px;
                background-color: #F5F5F7;
                border-radius: 8px;
                margin: 5px 0;
                font-size: 12px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def _test_connection(self):
        """Testa conexão com o webhook"""
        url = self.url_input.text().strip()

        if not url:
            self._set_status("❌ Digite uma URL válida", "error")
            return

        # Normaliza URL
        test_url = self._normalize_url(url)

        try:
            self.status_label.setText("🔄 Testando conexão...")
            QApplication.processEvents()  # Atualiza a UI

            response = requests.get(test_url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                self._set_status(f"✅ Conectado! {total} requisições encontradas", "success")
            else:
                self._set_status(f"❌ Erro HTTP: {response.status_code}", "error")

        except requests.exceptions.Timeout:
            self._set_status("❌ Timeout: Webhook não responde", "error")
        except requests.exceptions.ConnectionError:
            self._set_status("❌ Erro de conexão: Verifique a URL", "error")
        except json.JSONDecodeError:
            self._set_status("❌ Resposta inválida do webhook", "error")
        except Exception as e:
            self._set_status(f"❌ Erro: {str(e)[:50]}...", "error")

    def _normalize_url(self, url):
        """Normaliza a URL do webhook"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        if not url.endswith('/requisicoes'):
            if url.endswith('/'):
                url += 'requisicoes'
            else:
                url += '/requisicoes'

        return url

    def _set_status(self, message, status_type):
        """Define o status com cor apropriada"""
        colors = {
            "success": {"bg": "#E8F5E8", "color": "#2E7D32"},
            "error": {"bg": "#FFEBEE", "color": "#D32F2F"},
            "info": {"bg": "#F5F5F7", "color": "#666"}
        }

        color_config = colors.get(status_type, colors["info"])

        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color_config["color"]};
                padding: 12px;
                background-color: {color_config["bg"]};
                border-radius: 8px;
                margin: 5px 0;
                font-size: 12px;
            }}
        """)

    def _connect_webhook(self):
        """Conecta ao webhook e abre interface principal"""
        url = self.url_input.text().strip()

        if not url:
            self._set_status("❌ Digite uma URL válida", "error")
            return

        # Remove /requisicoes se presente para usar como base
        base_url = url
        if base_url.endswith('/requisicoes'):
            base_url = base_url[:-12]
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        # Cria e mostra a interface principal
        self.main_window = ChatInterface(base_url)
        self.main_window.show()

        # Fecha a janela de configuração
        self.close()


def main():
    """Função principal da aplicação"""
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    # Define ícone da aplicação (se disponível)
    try:
        app.setWindowIcon(QIcon("whatsapp_icon.png"))
    except:
        pass

    # Cria e exibe a janela de configuração
    config_window = ConfigWindow()
    config_window.show()

    # Inicia o loop da aplicação
    sys.exit(app.exec())


if __name__ == '__main__':
    main()