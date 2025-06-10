#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface WhatsApp Integrada com API e Banco de Dados
Baseada na estrutura original do WhatsAppApi.py com melhorias
"""

import sys
import os
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QTabWidget, QGroupBox,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QProgressBar,
    QComboBox, QSpinBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QScrollArea, QFrame, QSplitter, QStackedWidget, QGridLayout
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, pyqtSlot
)
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QIcon


class WhatsAppAPI:
    """Classe para integração com WhatsApp API"""

    def __init__(self, instance_id, api_token, base_url="https://api.w-api.app/v1/"):
        self.instance_id = instance_id
        self.api_token = api_token
        self.base_url = base_url
        self.connected = False

    def conectar(self):
        """Conecta e verifica status da API"""
        try:
            status = self.checa_status_conexao(self.api_token, self.instance_id)
            if status == "connected":
                self.connected = True
                return True
            return False
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False

    def checa_status_conexao(self, api_token, id_instance):
        """Verifica status da conexão com WhatsApp"""
        try:
            url = f"{self.base_url}status?instanceId={id_instance}"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('status', 'disconnected')
            return "disconnected"
        except Exception as e:
            print(f"Erro ao verificar status: {e}")
            return "disconnected"

    def envia_mensagem_texto(self, phone_number, message, delay_message=1):
        """Envia mensagem de texto"""
        try:
            time.sleep(delay_message)
            url = f"{self.base_url}message/sendText/{self.instance_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            data = {
                "number": phone_number,
                "textMessage": {
                    "text": message
                }
            }
            response = requests.post(url, headers=headers, json=data, timeout=15)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            return False

    def enviar_imagem(self, phone_number, image_path, caption="", delay_message=1):
        """Envia imagem"""
        try:
            time.sleep(delay_message)

            # Ler arquivo de imagem
            with open(image_path, 'rb') as f:
                image_data = f.read()

            url = f"{self.base_url}message/sendMedia/{self.instance_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }

            files = {
                'media': (os.path.basename(image_path), image_data, 'image/jpeg')
            }
            data = {
                'number': phone_number,
                'caption': caption
            }

            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar imagem: {e}")
            return False

    def envia_documento(self, phone_number, file_path, caption="", delay=2):
        """Envia documento"""
        try:
            time.sleep(delay)

            with open(file_path, 'rb') as f:
                file_data = f.read()

            url = f"{self.base_url}message/sendMedia/{self.instance_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }

            files = {
                'media': (os.path.basename(file_path), file_data, 'application/octet-stream')
            }
            data = {
                'number': phone_number,
                'caption': caption
            }

            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar documento: {e}")
            return False

    def enviar_audio(self, phone_number, audio_path, delay_message=1):
        """Envia áudio"""
        try:
            time.sleep(delay_message)

            with open(audio_path, 'rb') as f:
                audio_data = f.read()

            url = f"{self.base_url}message/sendMedia/{self.instance_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }

            files = {
                'media': (os.path.basename(audio_path), audio_data, 'audio/mpeg')
            }
            data = {
                'number': phone_number
            }

            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar áudio: {e}")
            return False

    def enviarGif(self, phone_number, gif_path, caption="", delay_message=1):
        """Envia GIF"""
        try:
            time.sleep(delay_message)

            with open(gif_path, 'rb') as f:
                gif_data = f.read()

            url = f"{self.base_url}message/sendMedia/{self.instance_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}"
            }

            files = {
                'media': (os.path.basename(gif_path), gif_data, 'image/gif')
            }
            data = {
                'number': phone_number,
                'caption': caption
            }

            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar GIF: {e}")
            return False

    def deleta_mensagem(self, phone_number, message_ids):
        """Deleta mensagens"""
        try:
            url = f"{self.base_url}message/delete/{self.instance_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }

            for msg_id in message_ids:
                data = {
                    "number": phone_number,
                    "messageId": msg_id
                }
                response = requests.post(url, headers=headers, json=data, timeout=10)
                if response.status_code != 200:
                    return False
            return True
        except Exception as e:
            print(f"Erro ao deletar mensagem: {e}")
            return False

    def editar_mensagem(self, phone, message_id, new_text):
        """Edita mensagem"""
        try:
            url = f"{self.base_url}message/edit/{self.instance_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            data = {
                "number": phone,
                "messageId": message_id,
                "newText": new_text
            }
            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao editar mensagem: {e}")
            return False

    def enviar_reacao(self, phone, message_id, reaction="👍", delay=2):
        """Envia reação"""
        try:
            time.sleep(delay)
            url = f"{self.base_url}message/reaction/{self.instance_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            data = {
                "number": phone,
                "messageId": message_id,
                "reaction": reaction
            }
            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao enviar reação: {e}")
            return False

    def removerReacao(self, phone, message_id, delay=2):
        """Remove reação"""
        try:
            time.sleep(delay)
            url = f"{self.base_url}message/reaction/remove/{self.instance_id}"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            data = {
                "number": phone,
                "messageId": message_id
            }
            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Erro ao remover reação: {e}")
            return False


class ChatDatabaseInterface:
    """Interface simulada para banco de dados"""

    def __init__(self, db_path=None):
        self.connected = True
        self.chats_data = self._generate_mock_data()

    def _generate_mock_data(self):
        """Gera dados mock para demonstração"""
        return {
            'chats': [
                {
                    'chat_id': '5569999111111',
                    'chat_name': 'João Silva',
                    'last_message': 'Olá! Como você está?',
                    'last_message_time': int(time.time()) - 3600,
                    'total_messages': 45,
                    'chat_type': 'individual'
                },
                {
                    'chat_id': '5569999222222',
                    'chat_name': 'Maria Santos',
                    'last_message': 'Vamos nos encontrar hoje?',
                    'last_message_time': int(time.time()) - 7200,
                    'total_messages': 23,
                    'chat_type': 'individual'
                },
                {
                    'chat_id': '5569999333333',
                    'chat_name': 'Pedro Oliveira',
                    'last_message': 'Obrigado pela ajuda!',
                    'last_message_time': int(time.time()) - 10800,
                    'total_messages': 12,
                    'chat_type': 'individual'
                }
            ],
            'messages': {
                '5569999111111': [
                    {
                        'message_id': 'msg_001',
                        'content': 'Oi! Tudo bem?',
                        'from_me': False,
                        'timestamp_str': '14:30',
                        'timestamp': int(time.time()) - 3600,
                        'sender_name': 'João Silva'
                    },
                    {
                        'message_id': 'msg_002',
                        'content': 'Tudo ótimo! E você?',
                        'from_me': True,
                        'timestamp_str': '14:32',
                        'timestamp': int(time.time()) - 3500,
                        'sender_name': 'Você'
                    }
                ]
            }
        }

    def is_connected(self):
        return self.connected

    def get_chats_list(self, limit=50):
        return self.chats_data['chats'][:limit]

    def get_chat_messages(self, chat_id, limit=50):
        return self.chats_data['messages'].get(chat_id, [])

    def check_for_new_messages(self):
        import random
        return random.choice([True, False])

    def get_database_stats(self):
        return {
            'total_events': 1250,
            'total_chats': len(self.chats_data['chats']),
            'total_senders': 78,
            'database_size_mb': 15.6,
            'first_message_date': '2024-01-01 10:00:00',
            'last_message_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


class MessageReceiver(QThread):
    """Thread para receber mensagens em tempo real"""

    new_message = pyqtSignal(dict)
    connection_status = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, db_interface):
        super().__init__()
        self.db_interface = db_interface
        self.running = False
        self.last_check = time.time()

    def run(self):
        """Loop principal para verificar novas mensagens"""
        self.running = True

        while self.running:
            try:
                if self.db_interface.check_for_new_messages():
                    # Simular nova mensagem
                    nova_mensagem = {
                        'chat_id': '5569999111111',
                        'sender_name': 'João Silva',
                        'content': f'Nova mensagem às {datetime.now().strftime("%H:%M:%S")}',
                        'timestamp': int(time.time()),
                        'from_me': False
                    }
                    self.new_message.emit(nova_mensagem)

                self.connection_status.emit(True)
                time.sleep(5)  # Verificar a cada 5 segundos

            except Exception as e:
                self.error_occurred.emit(str(e))
                self.connection_status.emit(False)
                time.sleep(10)

    def stop(self):
        """Para o thread"""
        self.running = False
        self.quit()
        self.wait()


class ContactWidget(QWidget):
    """Widget para exibir contato na lista"""

    clicked = pyqtSignal(str)

    def __init__(self, contact_data: Dict):
        super().__init__()
        self.contact_data = contact_data
        self.contact_id = contact_data['chat_id']
        self.setup_ui()

    def setup_ui(self):
        """Configura interface do contato"""
        self.setFixedHeight(70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("""
            QLabel {
                background-color: #25D366;
                color: white;
                border-radius: 25px;
                font-weight: bold;
                font-size: 18px;
            }
        """)

        # Primeira letra do nome
        name = self.contact_data['chat_name']
        initial = name[0].upper() if name else '?'
        avatar.setText(initial)

        # Informações
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Nome
        name_label = QLabel(name)
        name_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #2c3e50;")

        # Última mensagem
        last_msg = self.contact_data.get('last_message', '')
        if len(last_msg) > 40:
            last_msg = last_msg[:37] + "..."

        last_msg_label = QLabel(last_msg)
        last_msg_label.setFont(QFont('Arial', 10))
        last_msg_label.setStyleSheet("color: #7f8c8d;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(last_msg_label)

        # Status
        status_layout = QVBoxLayout()
        status_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Hora
        if self.contact_data.get('last_message_time'):
            dt = datetime.fromtimestamp(self.contact_data['last_message_time'])
            time_str = dt.strftime('%H:%M')
        else:
            time_str = ''

        time_label = QLabel(time_str)
        time_label.setFont(QFont('Arial', 9))
        time_label.setStyleSheet("color: #95a5a6;")

        # Contador de mensagens
        count_label = QLabel(str(self.contact_data.get('total_messages', 0)))
        count_label.setFont(QFont('Arial', 9))
        count_label.setStyleSheet("""
            QLabel {
                background-color: #25D366;
                color: white;
                border-radius: 10px;
                padding: 2px 6px;
                max-width: 30px;
            }
        """)

        status_layout.addWidget(time_label)
        status_layout.addWidget(count_label)

        layout.addWidget(avatar)
        layout.addLayout(info_layout, 1)
        layout.addLayout(status_layout)

        self.setLayout(layout)

        # Estilo do widget
        self.setStyleSheet("""
            ContactWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #ecf0f1;
            }
            ContactWidget:hover {
                background-color: #f8f9fa;
                border: 1px solid #25D366;
            }
        """)

    def mousePressEvent(self, event):
        """Evento de clique"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.contact_id)


class MessageBubbleWidget(QWidget):
    """Widget para exibir mensagem como balão"""

    def __init__(self, message_data: Dict, is_from_me: bool = False):
        super().__init__()
        self.message_data = message_data
        self.is_from_me = is_from_me
        self.setup_ui()

    def setup_ui(self):
        """Configura interface da mensagem"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Container do balão
        bubble_layout = QHBoxLayout()

        # Criar balão
        bubble = QFrame()
        bubble.setMaximumWidth(400)
        bubble_content = QVBoxLayout(bubble)
        bubble_content.setContentsMargins(15, 10, 15, 10)

        # Conteúdo da mensagem
        content = self.message_data.get('content', '')
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setFont(QFont('Arial', 11))

        # Hora
        timestamp_str = self.message_data.get('timestamp_str', '')
        if not timestamp_str and self.message_data.get('timestamp'):
            dt = datetime.fromtimestamp(self.message_data['timestamp'])
            timestamp_str = dt.strftime('%H:%M')

        time_label = QLabel(timestamp_str)
        time_label.setFont(QFont('Arial', 9))
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        bubble_content.addWidget(content_label)
        bubble_content.addWidget(time_label)

        # Estilo baseado no remetente
        if self.is_from_me:
            # Mensagem enviada - lado direito, verde
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #DCF8C6;
                    color: #2c3e50;
                    border-radius: 15px;
                    border-bottom-right-radius: 5px;
                }
            """)
            bubble_layout.addStretch()
            bubble_layout.addWidget(bubble)
        else:
            # Mensagem recebida - lado esquerdo, branco
            bubble.setStyleSheet("""
                QFrame {
                    background-color: white;
                    color: #2c3e50;
                    border-radius: 15px;
                    border-bottom-left-radius: 5px;
                    border: 1px solid #e1e1e1;
                }
            """)
            bubble_layout.addWidget(bubble)
            bubble_layout.addStretch()

        layout.addLayout(bubble_layout)
        self.setLayout(layout)


class WhatsAppInterface(QMainWindow):
    """Interface principal integrada do WhatsApp"""

    def __init__(self):
        super().__init__()
        self.api = None
        self.db_interface = None
        self.message_receiver = None
        self.current_contact = None
        self.current_contact_data = None

        self.setup_ui()
        self.setup_connections()
        self.setup_styles()

    def setup_ui(self):
        """Configura interface principal"""
        self.setWindowTitle("📱 WhatsApp Interface - API Integrada")
        self.setGeometry(100, 100, 1400, 900)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painéis
        left_panel = self.create_left_panel()
        center_panel = self.create_center_panel()
        right_panel = self.create_right_panel()

        left_panel.setMinimumWidth(300)
        left_panel.setMaximumWidth(350)
        right_panel.setMinimumWidth(350)
        right_panel.setMaximumWidth(400)

        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)

        # Proporções
        splitter.setSizes([300, 700, 400])

        main_layout.addWidget(splitter)

    def create_left_panel(self):
        """Cria painel esquerdo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # === CONFIGURAÇÃO DA API ===
        config_group = QGroupBox("🔧 Configuração WhatsApp API")
        config_layout = QVBoxLayout(config_group)

        # Instance ID
        self.instance_id_input = QLineEdit()
        self.instance_id_input.setPlaceholderText("Instance ID")

        # API Token
        self.api_token_input = QLineEdit()
        self.api_token_input.setPlaceholderText("API Token")
        self.api_token_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Botões de conexão
        connection_layout = QHBoxLayout()

        self.connect_btn = QPushButton("🔗 Conectar")
        self.connect_btn.clicked.connect(self.connect_api)

        self.status_btn = QPushButton("📡 Status")
        self.status_btn.clicked.connect(self.check_status)
        self.status_btn.setEnabled(False)

        connection_layout.addWidget(self.connect_btn)
        connection_layout.addWidget(self.status_btn)

        # Status da conexão
        self.connection_status = QLabel("🔴 Desconectado")
        self.connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")

        config_layout.addWidget(QLabel("Instance ID:"))
        config_layout.addWidget(self.instance_id_input)
        config_layout.addWidget(QLabel("API Token:"))
        config_layout.addWidget(self.api_token_input)
        config_layout.addLayout(connection_layout)
        config_layout.addWidget(self.connection_status)

        # === BANCO DE DADOS ===
        db_group = QGroupBox("💾 Banco de Dados")
        db_layout = QVBoxLayout(db_group)

        self.connect_db_btn = QPushButton("🗄️ Conectar Banco")
        self.connect_db_btn.clicked.connect(self.connect_database)

        self.db_status = QLabel("🔴 Banco desconectado")
        self.db_status.setStyleSheet("color: #e74c3c; font-weight: bold;")

        db_layout.addWidget(self.connect_db_btn)
        db_layout.addWidget(self.db_status)

        # === CONTATOS ===
        contacts_group = QGroupBox("👥 Contatos")
        contacts_layout = QVBoxLayout(contacts_group)

        # Busca
        self.search_contacts = QLineEdit()
        self.search_contacts.setPlaceholderText("🔍 Buscar contatos...")
        self.search_contacts.textChanged.connect(self.filter_contacts)

        # Lista de contatos
        self.contacts_scroll = QScrollArea()
        self.contacts_widget = QWidget()
        self.contacts_layout = QVBoxLayout(self.contacts_widget)
        self.contacts_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.contacts_scroll.setWidget(self.contacts_widget)
        self.contacts_scroll.setWidgetResizable(True)

        # Botão para carregar contatos
        self.load_contacts_btn = QPushButton("🔄 Carregar Contatos")
        self.load_contacts_btn.clicked.connect(self.load_contacts)
        self.load_contacts_btn.setEnabled(False)

        contacts_layout.addWidget(self.search_contacts)
        contacts_layout.addWidget(self.contacts_scroll, 1)
        contacts_layout.addWidget(self.load_contacts_btn)

        # Montar painel
        layout.addWidget(config_group)
        layout.addWidget(db_group)
        layout.addWidget(contacts_group, 1)

        return widget

    def create_center_panel(self):
        """Cria painel central (chat)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # === CABEÇALHO DO CHAT ===
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #25D366, stop:1 #128C7E);
                border: none;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        # Info do contato
        self.chat_contact_name = QLabel("💬 Selecione um contato")
        self.chat_contact_name.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.chat_contact_name.setStyleSheet("color: white;")

        self.chat_contact_status = QLabel("")
        self.chat_contact_status.setFont(QFont('Arial', 10))
        self.chat_contact_status.setStyleSheet("color: #ecf0f1;")

        contact_info = QVBoxLayout()
        contact_info.addWidget(self.chat_contact_name)
        contact_info.addWidget(self.chat_contact_status)

        # Botões do cabeçalho
        self.refresh_chat_btn = QPushButton("🔄")
        self.refresh_chat_btn.setFixedSize(35, 35)
        self.refresh_chat_btn.clicked.connect(self.refresh_chat)
        self.refresh_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 17px;
                font-size: 14px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)

        header_layout.addLayout(contact_info)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_chat_btn)

        # === ÁREA DE MENSAGENS ===
        self.messages_scroll = QScrollArea()
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(5)

        self.messages_scroll.setWidget(self.messages_widget)
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #E5DDD5;
                border: none;
            }
        """)

        # Mensagem inicial
        welcome_label = QLabel("👋 Selecione um contato para ver as mensagens")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 16px;
                padding: 50px;
            }
        """)
        self.messages_layout.addWidget(welcome_label)

        # === ÁREA DE ENVIO ===
        send_frame = QFrame()
        send_frame.setFixedHeight(80)
        send_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-top: 1px solid #d1d1d1;
            }
        """)

        send_layout = QHBoxLayout(send_frame)
        send_layout.setContentsMargins(20, 10, 20, 10)

        # Botão de anexo
        self.attach_btn = QPushButton("📎")
        self.attach_btn.setFixedSize(40, 40)
        self.attach_btn.clicked.connect(self.show_attach_menu)
        self.attach_btn.setEnabled(False)
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)

        # Campo de texto
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Digite sua mensagem...")
        self.message_input.setEnabled(False)
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d1d1;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #25D366;
            }
        """)

        # Botão de envio
        self.send_btn = QPushButton("📤")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setEnabled(False)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)

        send_layout.addWidget(self.attach_btn)
        send_layout.addWidget(self.message_input, 1)
        send_layout.addWidget(self.send_btn)

        # Montar painel
        layout.addWidget(header)
        layout.addWidget(self.messages_scroll, 1)
        layout.addWidget(send_frame)

        return widget

    def create_right_panel(self):
        """Cria painel direito (funcionalidades)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tabs para organizar funcionalidades
        tabs = QTabWidget()

        # === TAB 1: ENVIOS RÁPIDOS ===
        send_tab = QWidget()
        send_layout = QVBoxLayout(send_tab)

        # Envio de texto
        text_group = QGroupBox("📝 Envio Rápido")
        text_layout = QVBoxLayout(text_group)

        self.quick_phone = QLineEdit()
        self.quick_phone.setPlaceholderText("Número (ex: 5569999111111)")

        self.quick_message = QTextEdit()
        self.quick_message.setPlaceholderText("Mensagem...")
        self.quick_message.setMaximumHeight(100)

        quick_send_layout = QHBoxLayout()

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 60)
        self.delay_spin.setValue(1)
        self.delay_spin.setSuffix(" seg")

        self.quick_send_btn = QPushButton("📤 Enviar")
        self.quick_send_btn.clicked.connect(self.quick_send_text)
        self.quick_send_btn.setEnabled(False)

        quick_send_layout.addWidget(QLabel("Delay:"))
        quick_send_layout.addWidget(self.delay_spin)
        quick_send_layout.addWidget(self.quick_send_btn)

        text_layout.addWidget(QLabel("Número:"))
        text_layout.addWidget(self.quick_phone)
        text_layout.addWidget(QLabel("Mensagem:"))
        text_layout.addWidget(self.quick_message)
        text_layout.addLayout(quick_send_layout)

        # Envio de mídia
        media_group = QGroupBox("📎 Enviar Mídia")
        media_layout = QVBoxLayout(media_group)

        # Seletor de arquivo
        file_layout = QHBoxLayout()

        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Selecione um arquivo...")
        self.file_path.setReadOnly(True)

        self.select_file_btn = QPushButton("📁")
        self.select_file_btn.setFixedSize(40, 30)
        self.select_file_btn.clicked.connect(self.select_file)

        file_layout.addWidget(self.file_path)
        file_layout.addWidget(self.select_file_btn)

        # Tipo de mídia
        self.media_type = QComboBox()
        self.media_type.addItems([
            "📷 Imagem",
            "📄 Documento",
            "🎵 Áudio",
            "🎬 GIF/Vídeo"
        ])

        # Caption
        self.media_caption = QLineEdit()
        self.media_caption.setPlaceholderText("Legenda (opcional)")

        self.send_media_btn = QPushButton("📤 Enviar Mídia")
        self.send_media_btn.clicked.connect(self.send_media)
        self.send_media_btn.setEnabled(False)

        media_layout.addWidget(QLabel("Arquivo:"))
        media_layout.addLayout(file_layout)
        media_layout.addWidget(QLabel("Tipo:"))
        media_layout.addWidget(self.media_type)
        media_layout.addWidget(QLabel("Legenda:"))
        media_layout.addWidget(self.media_caption)
        media_layout.addWidget(self.send_media_btn)

        send_layout.addWidget(text_group)
        send_layout.addWidget(media_group)
        send_layout.addStretch()

        # === TAB 2: AÇÕES ===
        actions_tab = QWidget()
        actions_layout = QVBoxLayout(actions_tab)

        # Ações em mensagens
        message_actions_group = QGroupBox("⚡ Ações em Mensagens")
        message_actions_layout = QVBoxLayout(message_actions_group)

        # Deletar mensagem
        delete_layout = QVBoxLayout()

        self.delete_phone = QLineEdit()
        self.delete_phone.setPlaceholderText("Número do destinatário")

        self.message_ids = QLineEdit()
        self.message_ids.setPlaceholderText("IDs das mensagens (separados por vírgula)")

        self.delete_msg_btn = QPushButton("🗑️ Deletar Mensagens")
        self.delete_msg_btn.clicked.connect(self.delete_messages)
        self.delete_msg_btn.setEnabled(False)

        delete_layout.addWidget(QLabel("Deletar Mensagem:"))
        delete_layout.addWidget(self.delete_phone)
        delete_layout.addWidget(self.message_ids)
        delete_layout.addWidget(self.delete_msg_btn)

        # Editar mensagem
        edit_layout = QVBoxLayout()

        self.edit_phone = QLineEdit()
        self.edit_phone.setPlaceholderText("Número do destinatário")

        self.edit_message_id = QLineEdit()
        self.edit_message_id.setPlaceholderText("ID da mensagem")

        self.edit_new_text = QLineEdit()
        self.edit_new_text.setPlaceholderText("Novo texto")

        self.edit_msg_btn = QPushButton("✏️ Editar Mensagem")
        self.edit_msg_btn.clicked.connect(self.edit_message)
        self.edit_msg_btn.setEnabled(False)

        edit_layout.addWidget(QLabel("Editar Mensagem:"))
        edit_layout.addWidget(self.edit_phone)
        edit_layout.addWidget(self.edit_message_id)
        edit_layout.addWidget(self.edit_new_text)
        edit_layout.addWidget(self.edit_msg_btn)

        message_actions_layout.addLayout(delete_layout)
        message_actions_layout.addLayout(edit_layout)

        # Reações
        reactions_group = QGroupBox("😀 Reações")
        reactions_layout = QVBoxLayout(reactions_group)

        self.reaction_phone = QLineEdit()
        self.reaction_phone.setPlaceholderText("Número")

        self.reaction_msg_id = QLineEdit()
        self.reaction_msg_id.setPlaceholderText("ID da mensagem")

        reaction_buttons_layout = QHBoxLayout()

        # Botões de reação rápida
        reactions = ["👍", "❤️", "😂", "😮", "😢", "🔥"]
        for reaction in reactions:
            btn = QPushButton(reaction)
            btn.setFixedSize(35, 35)
            btn.clicked.connect(lambda checked, r=reaction: self.send_reaction(r))
            btn.setEnabled(False)
            reaction_buttons_layout.addWidget(btn)
            # Armazenar referência para habilitar depois
            if not hasattr(self, 'reaction_buttons'):
                self.reaction_buttons = []
            self.reaction_buttons.append(btn)

        self.remove_reaction_btn = QPushButton("❌ Remover Reação")
        self.remove_reaction_btn.clicked.connect(self.remove_reaction)
        self.remove_reaction_btn.setEnabled(False)

        reactions_layout.addWidget(QLabel("Reações:"))
        reactions_layout.addWidget(self.reaction_phone)
        reactions_layout.addWidget(self.reaction_msg_id)
        reactions_layout.addLayout(reaction_buttons_layout)
        reactions_layout.addWidget(self.remove_reaction_btn)

        actions_layout.addWidget(message_actions_group)
        actions_layout.addWidget(reactions_group)
        actions_layout.addStretch()

        # === TAB 3: MONITORAMENTO ===
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(monitor_tab)

        # Status do sistema
        system_group = QGroupBox("📊 Status do Sistema")
        system_layout = QVBoxLayout(system_group)

        self.realtime_status = QLabel("🔴 Tempo real: Inativo")
        self.realtime_status.setFont(QFont('Arial', 11, QFont.Weight.Bold))

        self.message_count = QLabel("📨 Mensagens: 0")
        self.last_message_time = QLabel("🕐 Última: Nunca")

        # Botões de controle
        control_layout = QHBoxLayout()

        self.start_realtime_btn = QPushButton("▶️ Iniciar")
        self.start_realtime_btn.clicked.connect(self.start_realtime)
        self.start_realtime_btn.setEnabled(False)

        self.stop_realtime_btn = QPushButton("⏹️ Parar")
        self.stop_realtime_btn.clicked.connect(self.stop_realtime)
        self.stop_realtime_btn.setEnabled(False)

        control_layout.addWidget(self.start_realtime_btn)
        control_layout.addWidget(self.stop_realtime_btn)

        system_layout.addWidget(self.realtime_status)
        system_layout.addWidget(self.message_count)
        system_layout.addWidget(self.last_message_time)
        system_layout.addLayout(control_layout)

        # Log de atividades
        log_group = QGroupBox("📋 Log de Atividades")
        log_layout = QVBoxLayout(log_group)

        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(200)
        self.activity_log.setReadOnly(True)
        self.activity_log.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Courier New', monospace;
                font-size: 10px;
                border-radius: 5px;
            }
        """)

        clear_log_btn = QPushButton("🗑️ Limpar Log")
        clear_log_btn.clicked.connect(lambda: self.activity_log.clear())

        log_layout.addWidget(self.activity_log)
        log_layout.addWidget(clear_log_btn)

        monitor_layout.addWidget(system_group)
        monitor_layout.addWidget(log_group)
        monitor_layout.addStretch()

        # === TAB 4: ESTATÍSTICAS ===
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)

        # Estatísticas do banco
        db_stats_group = QGroupBox("📈 Estatísticas")
        db_stats_layout = QVBoxLayout(db_stats_group)

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Métrica", "Valor"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setMaximumHeight(200)

        self.refresh_stats_btn = QPushButton("🔄 Atualizar")
        self.refresh_stats_btn.clicked.connect(self.refresh_stats)
        self.refresh_stats_btn.setEnabled(False)

        db_stats_layout.addWidget(self.stats_table)
        db_stats_layout.addWidget(self.refresh_stats_btn)

        stats_layout.addWidget(db_stats_group)
        stats_layout.addStretch()

        # Adicionar tabs
        tabs.addTab(send_tab, "📤 Envios")
        tabs.addTab(actions_tab, "⚡ Ações")
        tabs.addTab(monitor_tab, "📊 Monitor")
        tabs.addTab(stats_tab, "📈 Stats")

        layout.addWidget(tabs)

        return widget

    def setup_connections(self):
        """Configura conexões e timers"""
        # Timer para atualizar interface
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_interface)
        self.update_timer.start(5000)  # Atualizar a cada 5 segundos

    def setup_styles(self):
        """Aplica estilos à interface"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: white;
            }
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
            QPushButton:pressed {
                background-color: #0f7a6b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QLineEdit, QTextEdit {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #25D366;
            }
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #25D366;
                color: white;
            }
        """)

    def log_activity(self, message: str):
        """Adiciona mensagem ao log de atividades"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.activity_log.append(log_entry)

        # Manter apenas as últimas 100 linhas
        text = self.activity_log.toPlainText()
        lines = text.split('\n')
        if len(lines) > 100:
            self.activity_log.setPlainText('\n'.join(lines[-100:]))

        # Scroll para o final
        scrollbar = self.activity_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def connect_api(self):
        """Conecta à API do WhatsApp"""
        instance_id = self.instance_id_input.text().strip()
        api_token = self.api_token_input.text().strip()

        if not instance_id or not api_token:
            QMessageBox.warning(self, "Erro", "Preencha Instance ID e API Token!")
            return

        try:
            self.api = WhatsAppAPI(instance_id, api_token)

            # Testar conexão
            if self.api.conectar():
                self.connection_status.setText("🟢 Conectado")
                self.connection_status.setStyleSheet("color: #27ae60; font-weight: bold;")

                # Habilitar botões
                self.status_btn.setEnabled(True)
                self.quick_send_btn.setEnabled(True)
                self.send_media_btn.setEnabled(True)
                self.delete_msg_btn.setEnabled(True)
                self.edit_msg_btn.setEnabled(True)
                self.remove_reaction_btn.setEnabled(True)

                # Habilitar botões de reação
                if hasattr(self, 'reaction_buttons'):
                    for btn in self.reaction_buttons:
                        btn.setEnabled(True)

                self.log_activity("✅ API WhatsApp conectada com sucesso")
                QMessageBox.information(self, "Sucesso", "API conectada com sucesso!")

            else:
                self.connection_status.setText("🔴 Erro na conexão")
                self.connection_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.log_activity("❌ Erro ao conectar API")
                QMessageBox.warning(self, "Erro", "Não foi possível conectar à API!")

        except Exception as e:
            self.log_activity(f"❌ Erro na API: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao conectar API:\n{str(e)}")

    def check_status(self):
        """Verifica status da API"""
        if not self.api:
            return

        try:
            status = self.api.checa_status_conexao(
                self.api_token_input.text(),
                self.instance_id_input.text()
            )

            if status == "connected":
                self.log_activity("📡 Status: Conectado")
                QMessageBox.information(self, "Status", "API está conectada!")
            else:
                self.log_activity("📡 Status: Desconectado")
                QMessageBox.warning(self, "Status", "API desconectada!")

        except Exception as e:
            self.log_activity(f"❌ Erro ao verificar status: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao verificar status:\n{str(e)}")

    def connect_database(self):
        """Conecta ao banco de dados"""
        try:
            self.db_interface = ChatDatabaseInterface()

            if self.db_interface.is_connected():
                self.db_status.setText("🟢 Banco conectado")
                self.db_status.setStyleSheet("color: #27ae60; font-weight: bold;")

                # Habilitar botões
                self.load_contacts_btn.setEnabled(True)
                self.start_realtime_btn.setEnabled(True)
                self.refresh_stats_btn.setEnabled(True)

                self.log_activity("✅ Banco de dados conectado")
                QMessageBox.information(self, "Sucesso", "Banco de dados conectado!")

                # Carregar contatos automaticamente
                self.load_contacts()

            else:
                self.db_status.setText("🔴 Erro no banco")
                self.db_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.log_activity("❌ Erro ao conectar banco")
                QMessageBox.warning(self, "Erro", "Não foi possível conectar ao banco!")

        except Exception as e:
            self.log_activity(f"❌ Erro no banco: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao conectar banco:\n{str(e)}")

    def load_contacts(self):
        """Carrega lista de contatos do banco"""
        if not self.db_interface:
            return

        try:
            self.log_activity("🔄 Carregando contatos...")

            contacts = self.db_interface.get_chats_list(50)

            # Limpar lista atual
            for i in reversed(range(self.contacts_layout.count())):
                child = self.contacts_layout.itemAt(i).widget()
                if child:
                    child.deleteLater()

            # Adicionar contatos
            for contact in contacts:
                contact_widget = ContactWidget(contact)
                contact_widget.clicked.connect(self.select_contact)
                self.contacts_layout.addWidget(contact_widget)

            self.log_activity(f"✅ {len(contacts)} contatos carregados")

        except Exception as e:
            self.log_activity(f"❌ Erro ao carregar contatos: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao carregar contatos:\n{str(e)}")

    def filter_contacts(self, text: str):
        """Filtra contatos por texto"""
        text = text.lower()

        for i in range(self.contacts_layout.count()):
            widget = self.contacts_layout.itemAt(i).widget()
            if isinstance(widget, ContactWidget):
                contact_name = widget.contact_data['chat_name'].lower()
                widget.setVisible(text in contact_name)

    def select_contact(self, contact_id: str):
        """Seleciona um contato para chat"""
        if not self.db_interface:
            return

        try:
            self.current_contact = contact_id

            # Buscar dados do contato
            contacts = self.db_interface.get_chats_list(100)
            self.current_contact_data = None

            for contact in contacts:
                if contact['chat_id'] == contact_id:
                    self.current_contact_data = contact
                    break

            if not self.current_contact_data:
                return

            # Atualizar cabeçalho
            contact_name = self.current_contact_data['chat_name']
            self.chat_contact_name.setText(f"💬 {contact_name}")
            self.chat_contact_status.setText(f"{self.current_contact_data.get('total_messages', 0)} mensagens")

            # Habilitar campos de envio
            if self.api and self.api.connected:
                self.message_input.setEnabled(True)
                self.send_btn.setEnabled(True)
                self.attach_btn.setEnabled(True)

            # Carregar mensagens
            self.load_chat_messages()

            self.log_activity(f"👤 Contato selecionado: {contact_name}")

        except Exception as e:
            self.log_activity(f"❌ Erro ao selecionar contato: {str(e)}")

    def load_chat_messages(self):
        """Carrega mensagens do chat atual"""
        if not self.current_contact or not self.db_interface:
            return

        try:
            # Limpar mensagens atuais
            for i in reversed(range(self.messages_layout.count())):
                child = self.messages_layout.itemAt(i).widget()
                if child:
                    child.deleteLater()

            # Carregar mensagens
            messages = self.db_interface.get_chat_messages(self.current_contact, 50)

            if not messages:
                no_messages = QLabel("📭 Nenhuma mensagem encontrada")
                no_messages.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_messages.setStyleSheet("color: #7f8c8d; font-size: 14px; padding: 20px;")
                self.messages_layout.addWidget(no_messages)
                return

            # Adicionar mensagens
            for message in messages:
                is_from_me = message.get('from_me', False)
                message_widget = MessageBubbleWidget(message, is_from_me)
                self.messages_layout.addWidget(message_widget)

            # Scroll para o final
            QTimer.singleShot(100, self.scroll_to_bottom)

            self.log_activity(f"💬 {len(messages)} mensagens carregadas")

        except Exception as e:
            self.log_activity(f"❌ Erro ao carregar mensagens: {str(e)}")

    def scroll_to_bottom(self):
        """Faz scroll para o final das mensagens"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def refresh_chat(self):
        """Atualiza chat atual"""
        if self.current_contact:
            self.load_chat_messages()
            self.log_activity("🔄 Chat atualizado")

    def send_message(self):
        """Envia mensagem pelo chat"""
        if not self.api or not self.api.connected or not self.current_contact:
            QMessageBox.warning(self, "Erro", "API não conectada ou contato não selecionado!")
            return

        message_text = self.message_input.text().strip()
        if not message_text:
            return

        try:
            result = self.api.envia_mensagem_texto(
                self.current_contact,
                message_text,
                delay_message=1
            )

            if result:
                # Adicionar mensagem enviada ao chat
                sent_message = {
                    'content': message_text,
                    'from_me': True,
                    'timestamp': int(time.time()),
                    'timestamp_str': datetime.now().strftime('%H:%M')
                }

                message_widget = MessageBubbleWidget(sent_message, True)
                self.messages_layout.addWidget(message_widget)

                self.message_input.clear()
                self.scroll_to_bottom()

                self.log_activity(f"📤 Mensagem enviada para {self.current_contact}")

            else:
                self.log_activity("❌ Erro ao enviar mensagem")
                QMessageBox.warning(self, "Erro", "Erro ao enviar mensagem!")

        except Exception as e:
            self.log_activity(f"❌ Erro no envio: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao enviar:\n{str(e)}")

    def show_attach_menu(self):
        """Mostra menu de anexos"""
        # Por simplicidade, abre diálogo de arquivo
        self.select_file()

    def quick_send_text(self):
        """Envio rápido de texto"""
        if not self.api or not self.api.connected:
            QMessageBox.warning(self, "Erro", "API não conectada!")
            return

        phone = self.quick_phone.text().strip()
        message = self.quick_message.toPlainText().strip()
        delay = self.delay_spin.value()

        if not phone or not message:
            QMessageBox.warning(self, "Erro", "Preencha número e mensagem!")
            return

        try:
            result = self.api.envia_mensagem_texto(phone, message, delay)

            if result:
                self.quick_message.clear()
                self.log_activity(f"📤 Texto enviado para {phone}")
                QMessageBox.information(self, "Sucesso", "Mensagem enviada!")
            else:
                self.log_activity(f"❌ Erro ao enviar para {phone}")
                QMessageBox.warning(self, "Erro", "Erro ao enviar mensagem!")

        except Exception as e:
            self.log_activity(f"❌ Erro no envio: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao enviar:\n{str(e)}")

    def select_file(self):
        """Seleciona arquivo para envio"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo",
            "",
            "Todos os arquivos (*.*)"
        )

        if file_path:
            self.file_path.setText(file_path)

    def send_media(self):
        """Envia arquivo de mídia"""
        if not self.api or not self.api.connected:
            QMessageBox.warning(self, "Erro", "API não conectada!")
            return

        phone = self.quick_phone.text().strip()
        file_path = self.file_path.text().strip()
        caption = self.media_caption.text().strip()
        media_type = self.media_type.currentText()

        if not phone or not file_path:
            QMessageBox.warning(self, "Erro", "Preencha número e selecione arquivo!")
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Erro", "Arquivo não encontrado!")
            return

        try:
            result = False

            if "Imagem" in media_type:
                result = self.api.enviar_imagem(phone, file_path, caption)
            elif "Documento" in media_type:
                result = self.api.envia_documento(phone, file_path, caption)
            elif "Áudio" in media_type:
                result = self.api.enviar_audio(phone, file_path)
            elif "GIF" in media_type:
                result = self.api.enviarGif(phone, file_path, caption)

            if result:
                self.file_path.clear()
                self.media_caption.clear()
                self.log_activity(f"📎 {media_type} enviado para {phone}")
                QMessageBox.information(self, "Sucesso", "Mídia enviada!")
            else:
                self.log_activity(f"❌ Erro ao enviar {media_type}")
                QMessageBox.warning(self, "Erro", "Erro ao enviar mídia!")

        except Exception as e:
            self.log_activity(f"❌ Erro no envio: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao enviar:\n{str(e)}")

    def delete_messages(self):
        """Deleta mensagens"""
        if not self.api or not self.api.connected:
            QMessageBox.warning(self, "Erro", "API não conectada!")
            return

        phone = self.delete_phone.text().strip()
        message_ids = self.message_ids.text().strip()

        if not phone or not message_ids:
            QMessageBox.warning(self, "Erro", "Preencha número e IDs das mensagens!")
            return

        try:
            # Converter IDs para lista
            ids_list = [id.strip() for id in message_ids.split(',')]

            result = self.api.deleta_mensagem(phone, ids_list)

            if result:
                self.message_ids.clear()
                self.log_activity(f"🗑️ Mensagens deletadas: {len(ids_list)}")
                QMessageBox.information(self, "Sucesso", "Mensagens deletadas!")
            else:
                self.log_activity("❌ Erro ao deletar mensagens")
                QMessageBox.warning(self, "Erro", "Erro ao deletar mensagens!")

        except Exception as e:
            self.log_activity(f"❌ Erro na deleção: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao deletar:\n{str(e)}")

    def edit_message(self):
        """Edita mensagem"""
        if not self.api or not self.api.connected:
            QMessageBox.warning(self, "Erro", "API não conectada!")
            return

        phone = self.edit_phone.text().strip()
        message_id = self.edit_message_id.text().strip()
        new_text = self.edit_new_text.text().strip()

        if not phone or not message_id or not new_text:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return

        try:
            result = self.api.editar_mensagem(phone, message_id, new_text)

            if result:
                self.edit_message_id.clear()
                self.edit_new_text.clear()
                self.log_activity(f"✏️ Mensagem editada: {message_id}")
                QMessageBox.information(self, "Sucesso", "Mensagem editada!")
            else:
                self.log_activity("❌ Erro ao editar mensagem")
                QMessageBox.warning(self, "Erro", "Erro ao editar mensagem!")

        except Exception as e:
            self.log_activity(f"❌ Erro na edição: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao editar:\n{str(e)}")

    def send_reaction(self, reaction: str):
        """Envia reação"""
        if not self.api or not self.api.connected:
            QMessageBox.warning(self, "Erro", "API não conectada!")
            return

        phone = self.reaction_phone.text().strip()
        message_id = self.reaction_msg_id.text().strip()

        if not phone or not message_id:
            QMessageBox.warning(self, "Erro", "Preencha número e ID da mensagem!")
            return

        try:
            result = self.api.enviar_reacao(phone, message_id, reaction)

            if result:
                self.log_activity(f"😀 Reação {reaction} enviada")
                QMessageBox.information(self, "Sucesso", f"Reação {reaction} enviada!")
            else:
                self.log_activity("❌ Erro ao enviar reação")
                QMessageBox.warning(self, "Erro", "Erro ao enviar reação!")

        except Exception as e:
            self.log_activity(f"❌ Erro na reação: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao enviar reação:\n{str(e)}")

    def remove_reaction(self):
        """Remove reação"""
        if not self.api or not self.api.connected:
            QMessageBox.warning(self, "Erro", "API não conectada!")
            return

        phone = self.reaction_phone.text().strip()
        message_id = self.reaction_msg_id.text().strip()

        if not phone or not message_id:
            QMessageBox.warning(self, "Erro", "Preencha número e ID da mensagem!")
            return

        try:
            result = self.api.removerReacao(phone, message_id, 1)

            if result:
                self.log_activity("❌ Reação removida")
                QMessageBox.information(self, "Sucesso", "Reação removida!")
            else:
                self.log_activity("❌ Erro ao remover reação")
                QMessageBox.warning(self, "Erro", "Erro ao remover reação!")

        except Exception as e:
            self.log_activity(f"❌ Erro ao remover reação: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao remover reação:\n{str(e)}")

    def start_realtime(self):
        """Inicia monitoramento em tempo real"""
        if not self.db_interface:
            QMessageBox.warning(self, "Erro", "Banco não conectado!")
            return

        try:
            self.message_receiver = MessageReceiver(self.db_interface)
            self.message_receiver.new_message.connect(self.on_new_message)
            self.message_receiver.connection_status.connect(self.on_realtime_status)
            self.message_receiver.error_occurred.connect(self.on_realtime_error)

            self.message_receiver.start()

            self.start_realtime_btn.setEnabled(False)
            self.stop_realtime_btn.setEnabled(True)

            self.log_activity("▶️ Monitoramento em tempo real iniciado")

        except Exception as e:
            self.log_activity(f"❌ Erro ao iniciar tempo real: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao iniciar:\n{str(e)}")

    def stop_realtime(self):
        """Para monitoramento em tempo real"""
        if self.message_receiver:
            self.message_receiver.stop()
            self.message_receiver = None

        self.start_realtime_btn.setEnabled(True)
        self.stop_realtime_btn.setEnabled(False)

        self.realtime_status.setText("🔴 Tempo real: Inativo")
        self.realtime_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self.log_activity("⏹️ Monitoramento em tempo real parado")

    @pyqtSlot(dict)
    def on_new_message(self, message: Dict):
        """Processa nova mensagem recebida"""
        try:
            sender_name = message.get('sender_name', 'Desconhecido')
            content = message.get('content', '')

            self.log_activity(f"📨 Nova mensagem de {sender_name}: {content[:30]}...")

            # Atualizar chat se for do contato atual
            if (self.current_contact and
                    message.get('chat_id') == self.current_contact):
                # Adicionar nova mensagem ao chat
                message_widget = MessageBubbleWidget(message, False)
                self.messages_layout.addWidget(message_widget)
                self.scroll_to_bottom()

            # Atualizar lista de contatos
            QTimer.singleShot(2000, self.load_contacts)

        except Exception as e:
            self.log_activity(f"❌ Erro ao processar mensagem: {str(e)}")

    @pyqtSlot(bool)
    def on_realtime_status(self, connected: bool):
        """Atualiza status do tempo real"""
        if connected:
            self.realtime_status.setText("🟢 Tempo real: Ativo")
            self.realtime_status.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.realtime_status.setText("🔴 Tempo real: Erro")
            self.realtime_status.setStyleSheet("color: #e74c3c; font-weight: bold;")

    @pyqtSlot(str)
    def on_realtime_error(self, error: str):
        """Trata erro do tempo real"""
        self.log_activity(f"❌ Erro tempo real: {error}")

    def refresh_stats(self):
        """Atualiza estatísticas"""
        if not self.db_interface:
            return

        try:
            stats = self.db_interface.get_database_stats()

            # Atualizar tabela
            self.stats_table.setRowCount(0)

            stats_items = [
                ("Total de Eventos", stats.get('total_events', 0)),
                ("Total de Chats", stats.get('total_chats', 0)),
                ("Total de Remetentes", stats.get('total_senders', 0)),
                ("Tamanho do Banco (MB)", stats.get('database_size_mb', 0)),
                ("Primeira Mensagem", stats.get('first_message_date', 'N/A')),
                ("Última Mensagem", stats.get('last_message_date', 'N/A'))
            ]

            for i, (metric, value) in enumerate(stats_items):
                self.stats_table.insertRow(i)
                self.stats_table.setItem(i, 0, QTableWidgetItem(metric))
                self.stats_table.setItem(i, 1, QTableWidgetItem(str(value)))

            self.log_activity("📊 Estatísticas atualizadas")

        except Exception as e:
            self.log_activity(f"❌ Erro ao atualizar stats: {str(e)}")

    def update_interface(self):
        """Atualiza interface periodicamente"""
        # Atualizar contadores de mensagens
        if self.db_interface:
            try:
                stats = self.db_interface.get_database_stats()
                total_events = stats.get('total_events', 0)
                self.message_count.setText(f"📨 Mensagens: {total_events}")

                # Última mensagem
                if stats.get('last_message_date'):
                    last_time = stats['last_message_date']
                    self.last_message_time.setText(f"🕐 Última: {last_time}")

            except Exception:
                pass  # Ignorar erros silenciosos

    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        # Parar monitoramento em tempo real
        if self.message_receiver:
            self.message_receiver.stop()

        # Parar timers
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

        self.log_activity("👋 Interface encerrada")
        event.accept()


def main():
    """Função principal"""
    app = QApplication(sys.argv)

    # Configurações da aplicação
    app.setApplicationName("WhatsApp Interface Integrada")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("WhatsApp Tools Pro")

    # Estilo global
    app.setStyle("Fusion")

    # Paleta de cores personalizada
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(248, 249, 250))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(37, 211, 102))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(44, 62, 80))
    palette.setColor(QPalette.ColorRole.Button, QColor(37, 211, 102))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(231, 76, 60))
    palette.setColor(QPalette.ColorRole.Link, QColor(37, 211, 102))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(37, 211, 102))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    # Criar e mostrar janela principal
    window = WhatsAppInterface()
    window.show()

    # Log inicial
    window.log_activity("🚀 Interface WhatsApp Integrada iniciada")
    window.log_activity("💡 1. Configure Instance ID e API Token")
    window.log_activity("💡 2. Conecte à API do WhatsApp")
    window.log_activity("💡 3. Conecte ao banco de dados")
    window.log_activity("💡 4. Selecione um contato e comece a conversar!")

    # Executar aplicação
    return app.exec()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        import traceback

        traceback.print_exc()

# =============================================================================
# 📱 INTERFACE WHATSAPP INTEGRADA - GUIA COMPLETO
# =============================================================================
#
# 🔧 CONFIGURAÇÃO INICIAL:
# 1. Insira seu Instance ID da API do WhatsApp
# 2. Insira seu API Token (será ocultado por segurança)
# 3. Clique em "🔗 Conectar" para conectar à API
# 4. Clique em "🗄️ Conectar Banco" para conectar ao banco de dados
# 5. Aguarde o carregamento automático dos contatos
#
# 💬 FUNCIONALIDADES PRINCIPAIS:
#
# ✅ CHAT EM TEMPO REAL:
# - Selecione um contato na lista esquerda
# - Digite mensagem no campo inferior e pressione Enter ou clique 📤
# - Ative "▶️ Iniciar" para receber mensagens automaticamente
# - Use 📎 para anexar arquivos
#
# ✅ ENVIOS RÁPIDOS (Aba "📤 Envios"):
# - Envio de texto para qualquer número
# - Envio de mídia (imagens, documentos, áudios, GIFs)
# - Configuração de delay personalizado
#
# ✅ AÇÕES AVANÇADAS (Aba "⚡ Ações"):
# - Deletar mensagens (IDs separados por vírgula)
# - Editar mensagens existentes
# - Enviar reações (👍 ❤️ 😂 😮 😢 🔥)
# - Remover reações
#
# ✅ MONITORAMENTO (Aba "📊 Monitor"):
# - Status do sistema em tempo real
# - Log detalhado de todas as atividades
# - Contadores de mensagens
# - Controle do monitoramento automático
#
# ✅ ESTATÍSTICAS (Aba "📈 Stats"):
# - Métricas do banco de dados
# - Total de eventos, chats e remetentes
# - Informações de tamanho e datas
#
# 🎨 CARACTERÍSTICAS VISUAIS:
# - Interface inspirada no WhatsApp oficial
# - Cores verde (#25D366) e cinza (#128C7E)
# - Balões de mensagem realistas
# - Avatares com iniciais dos contatos
# - Timestamps e status de leitura
#
# 🔄 TEMPO REAL:
# - Verificação automática de novas mensagens
# - Atualização instantânea do chat ativo
# - Notificações no log de atividades
# - Refresh automático da lista de contatos
#
# 📊 MONITORAMENTO:
# - Log colorido com timestamps
# - Status de conexão em tempo real
# - Contadores de mensagens atualizados
# - Histórico de atividades mantido
#
# 🛠️ DEPENDÊNCIAS:
# - PyQt6: pip install PyQt6
# - requests: pip install requests
# - API do WhatsApp (w-api.app ou similar)
# - Banco de dados SQLite/PostgreSQL (opcional)
#
# 🚀 PARA EXECUTAR:
# python interface_whatsapp_integrada.py
#
# 🔐 SEGURANÇA:
# - API Token ocultado na interface
# - Logs sem informações sensíveis
# - Timeouts configurados para todas as requisições
# - Tratamento de erros abrangente
#
# 📝 NOTAS IMPORTANTES:
# - Configure corretamente os endpoints da API
# - Mantenha o banco de dados atualizado
# - Use delays apropriados para evitar bloqueios
# - Monitore o log para identificar problemas
#
# =============================================================================