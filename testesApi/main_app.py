#!/usr/bin/env python3
"""
Interface de Chat Moderna - PyQt6
Integração completa com Webhook WhatsApp
Design elegante e funcional para 2025
"""

import sys
import json
import requests
import threading
import time
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea,
    QFrame, QGraphicsDropShadowEffect, QMessageBox, QFileDialog,
    QMenu, QSystemTrayIcon, QSplitter, QListWidget, QListWidgetItem,
    QStackedWidget, QTextBrowser, QProgressBar, QSlider, QCheckBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QRect, QSize, QUrl, QObject
)
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QPainterPath, QColor, QIcon,
    QLinearGradient, QFontMetrics, QDesktopServices, QAction
)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


class MessageBubble(QFrame):
    """Balão de mensagem moderna com design elegante"""

    def __init__(self, text: str, is_sent: bool = False, timestamp: str = "",
                 sender_name: str = "", avatar_url: str = "", message_id: str = ""):
        super().__init__()
        self.text = text
        self.is_sent = is_sent
        self.timestamp = timestamp
        self.sender_name = sender_name
        self.avatar_url = avatar_url
        self.message_id = message_id
        self.is_read = False
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface do balão"""
        self.setMaximumWidth(400)
        self.setMinimumHeight(60)

        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Avatar
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(35, 35)
        self.avatar_label.setStyleSheet("""
            QLabel {
                border-radius: 17px;
                background-color: #E3F2FD;
                border: 2px solid #BBDEFB;
            }
        """)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setText(self.sender_name[:1].upper() if self.sender_name else "U")

        # Container da mensagem
        message_container = QVBoxLayout()

        # Nome do remetente (apenas para mensagens recebidas)
        if not self.is_sent and self.sender_name:
            name_label = QLabel(self.sender_name)
            name_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            name_label.setStyleSheet("color: #1976D2; margin-bottom: 2px;")
            message_container.addWidget(name_label)

        # Texto da mensagem
        self.message_label = QLabel(self.text)
        self.message_label.setWordWrap(True)
        self.message_label.setFont(QFont("Segoe UI", 10))
        self.message_label.setStyleSheet("color: #333; line-height: 1.4;")
        message_container.addWidget(self.message_label)

        # Container inferior (timestamp + status)
        bottom_layout = QHBoxLayout()

        # Timestamp
        time_label = QLabel(self.timestamp)
        time_label.setFont(QFont("Segoe UI", 8))
        time_label.setStyleSheet("color: #666;")
        bottom_layout.addWidget(time_label)

        bottom_layout.addStretch()

        # Status de leitura (apenas para mensagens enviadas)
        if self.is_sent:
            self.status_label = QLabel("✓✓")
            self.status_label.setFont(QFont("Segoe UI", 8))
            self.status_label.setStyleSheet("color: #4CAF50;")
            bottom_layout.addWidget(self.status_label)

        message_container.addLayout(bottom_layout)

        # Organizar layout baseado no tipo de mensagem
        if self.is_sent:
            layout.addStretch()
            layout.addLayout(message_container)
            layout.addWidget(self.avatar_label)
            self.setStyleSheet(self.get_sent_style())
        else:
            layout.addWidget(self.avatar_label)
            layout.addLayout(message_container)
            layout.addStretch()
            self.setStyleSheet(self.get_received_style())

        # Sombra
        self.add_shadow()

    def get_sent_style(self):
        """Estilo para mensagens enviadas"""
        return """
            MessageBubble {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #E3F2FD, stop:1 #BBDEFB);
                border-radius: 20px;
                border: 1px solid #90CAF9;
                margin: 5px;
            }
        """

    def get_received_style(self):
        """Estilo para mensagens recebidas"""
        return """
            MessageBubble {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #F5F5F5, stop:1 #EEEEEE);
                border-radius: 20px;
                border: 1px solid #E0E0E0;
                margin: 5px;
            }
        """

    def add_shadow(self):
        """Adiciona sombra suave ao balão"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

    def mark_as_read(self):
        """Marca mensagem como lida"""
        if self.is_sent and hasattr(self, 'status_label'):
            self.is_read = True
            self.status_label.setStyleSheet("color: #2196F3;")


class TypingIndicator(QFrame):
    """Indicador de digitação animado"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_animation()

    def setup_ui(self):
        """Configura interface do indicador"""
        self.setMaximumWidth(200)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border-radius: 20px;
                border: 1px solid #E0E0E0;
                margin: 5px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        # Avatar pequeno
        avatar = QLabel("...")
        avatar.setFixedSize(20, 20)
        avatar.setStyleSheet("""
            QLabel {
                border-radius: 10px;
                background-color: #BDBDBD;
                color: white;
                font-size: 8px;
            }
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Pontos animados
        self.dots_label = QLabel("●●●")
        self.dots_label.setFont(QFont("Segoe UI", 12))
        self.dots_label.setStyleSheet("color: #9E9E9E;")

        layout.addWidget(avatar)
        layout.addWidget(self.dots_label)
        layout.addStretch()

        # Sombra
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(1, 1)
        self.setGraphicsEffect(shadow)

    def setup_animation(self):
        """Configura animação dos pontos"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_dots)
        self.dot_states = ["●○○", "●●○", "●●●", "○●●", "○○●", "○○○"]
        self.current_state = 0

    def start_animation(self):
        """Inicia animação"""
        self.timer.start(300)

    def stop_animation(self):
        """Para animação"""
        self.timer.stop()

    def animate_dots(self):
        """Anima os pontos"""
        self.dots_label.setText(self.dot_states[self.current_state])
        self.current_state = (self.current_state + 1) % len(self.dot_states)


class ChatListItem(QFrame):
    """Item da lista de conversas"""

    def __init__(self, chat_id: str, name: str, last_message: str,
                 timestamp: str, unread_count: int = 0, avatar_url: str = ""):
        super().__init__()
        self.chat_id = chat_id
        self.name = name
        self.last_message = last_message
        self.timestamp = timestamp
        self.unread_count = unread_count
        self.avatar_url = avatar_url
        self.setup_ui()

    def setup_ui(self):
        """Configura interface do item"""
        self.setFixedHeight(70)
        self.setStyleSheet("""
            ChatListItem {
                background-color: transparent;
                border-bottom: 1px solid #E0E0E0;
                margin: 0px;
            }
            ChatListItem:hover {
                background-color: #F5F5F5;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)

        # Avatar
        avatar = QLabel()
        avatar.setFixedSize(45, 45)
        avatar.setStyleSheet("""
            QLabel {
                border-radius: 22px;
                background-color: #E3F2FD;
                border: 2px solid #BBDEFB;
                font-size: 16px;
                font-weight: bold;
                color: #1976D2;
            }
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setText(self.name[:1].upper() if self.name else "C")

        # Informações do chat
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        # Nome e timestamp
        top_layout = QHBoxLayout()
        name_label = QLabel(self.name)
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #212121;")

        time_label = QLabel(self.timestamp)
        time_label.setFont(QFont("Segoe UI", 9))
        time_label.setStyleSheet("color: #757575;")

        top_layout.addWidget(name_label)
        top_layout.addStretch()
        top_layout.addWidget(time_label)

        # Última mensagem e contador
        bottom_layout = QHBoxLayout()
        message_label = QLabel(self.last_message)
        message_label.setFont(QFont("Segoe UI", 9))
        message_label.setStyleSheet("color: #616161;")

        if self.unread_count > 0:
            unread_label = QLabel(str(self.unread_count))
            unread_label.setFixedSize(20, 20)
            unread_label.setStyleSheet("""
                QLabel {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 10px;
                    font-size: 8px;
                    font-weight: bold;
                }
            """)
            unread_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bottom_layout.addWidget(message_label)
            bottom_layout.addStretch()
            bottom_layout.addWidget(unread_label)
        else:
            bottom_layout.addWidget(message_label)
            bottom_layout.addStretch()

        info_layout.addLayout(top_layout)
        info_layout.addLayout(bottom_layout)

        layout.addWidget(avatar)
        layout.addLayout(info_layout)


class ServerDiscovery(QThread):
    """Thread para descobrir servidores webhook disponíveis"""

    server_found = pyqtSignal(str, str)  # URL, descrição
    discovery_status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.discovered_servers = set()

    def run(self):
        """Busca por servidores webhook"""
        self.discovery_status.emit("🔍 Procurando servidores webhook...")

        # URLs para testar
        test_urls = [
            "http://localhost:5000",
            "http://127.0.0.1:5000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

        # Buscar URLs ngrok ativas
        ngrok_urls = self.discover_ngrok_tunnels()
        test_urls.extend(ngrok_urls)

        for url in test_urls:
            if not self.running:
                break

            try:
                response = requests.get(f"{url}/status", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    if url not in self.discovered_servers:
                        self.discovered_servers.add(url)
                        description = f"Webhook ativo ({data.get('total_requisicoes', 0)} requisições)"
                        self.server_found.emit(url, description)

            except requests.RequestException:
                continue

        if not self.discovered_servers:
            self.discovery_status.emit("❌ Nenhum servidor webhook encontrado")
        else:
            self.discovery_status.emit(f"✅ {len(self.discovered_servers)} servidor(es) encontrado(s)")

    def discover_ngrok_tunnels(self) -> List[str]:
        """Descobre túneis ngrok ativos"""
        urls = []
        try:
            # Tentar acessar API local do ngrok
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                data = response.json()
                for tunnel in data.get('tunnels', []):
                    public_url = tunnel.get('public_url', '')
                    if public_url and 'https://' in public_url:
                        urls.append(public_url)
        except:
            pass
        return urls

    def stop(self):
        """Para a descoberta"""
        self.running = False


class WebhookListener(QThread):
    """Thread para escutar o webhook"""

    message_received = pyqtSignal(dict)
    status_received = pyqtSignal(dict)
    connection_status = pyqtSignal(bool, str)
    new_chat_created = pyqtSignal(str, str, str)  # chat_id, name, last_message

    def __init__(self, webhook_url: str):
        super().__init__()
        self.webhook_url = webhook_url
        self.running = True
        self.last_request_count = 0
        self.processed_messages = set()

    def run(self):
        """Monitora o webhook continuamente"""
        while self.running:
            try:
                # Verifica se há novas mensagens
                response = requests.get(f"{self.webhook_url}/requisicoes", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    current_count = data.get('total', 0)
                    self.connection_status.emit(True, f"Conectado ({current_count} req)")

                    # Processar apenas novas requisições
                    if current_count > self.last_request_count:
                        new_requests = data.get('requisicoes', [])[-5:]  # Últimas 5
                        for req in new_requests:
                            if req.get('json'):
                                self.process_webhook_data(req['json'])

                        self.last_request_count = current_count
                else:
                    self.connection_status.emit(False, f"Erro HTTP {response.status_code}")

            except requests.RequestException as e:
                self.connection_status.emit(False, f"Conexão perdida")
            except Exception as e:
                self.connection_status.emit(False, f"Erro: {str(e)}")

            time.sleep(1)  # Verifica a cada 1 segundo para ser mais responsivo

    def process_webhook_data(self, data: dict):
        """Processa dados do webhook"""
        message_id = data.get('messageId', '')

        # Evitar processamento duplicado
        if message_id and message_id in self.processed_messages:
            return

        if message_id:
            self.processed_messages.add(message_id)
            # Manter apenas os últimos 1000 IDs para evitar vazamento de memória
            if len(self.processed_messages) > 1000:
                self.processed_messages = set(list(self.processed_messages)[-500:])

        if data.get('event') == 'webhookDelivery':
            self.message_received.emit(data)
        elif data.get('event') == 'webhookStatus':
            self.status_received.emit(data)

    def stop(self):
        """Para o monitoramento"""
        self.running = False


class ModernChatInterface(QMainWindow):
    """Interface principal do chat"""

    def __init__(self):
        super().__init__()
        self.current_chat_id = None
        self.chats = {}  # Armazena conversas
        self.dark_mode = False
        self.webhook_url = None  # Será detectado automaticamente
        self.webhook_listener = None
        self.server_discovery = None
        self.available_servers = []
        self.setup_ui()
        self.discover_servers()
        self.apply_theme()

    def discover_servers(self):
        """Inicia descoberta de servidores"""
        self.server_discovery = ServerDiscovery()
        self.server_discovery.server_found.connect(self.on_server_found)
        self.server_discovery.discovery_status.connect(self.on_discovery_status)
        self.server_discovery.finished.connect(self.on_discovery_finished)
        self.server_discovery.start()

    def on_server_found(self, url: str, description: str):
        """Quando um servidor é encontrado"""
        self.available_servers.append({"url": url, "description": description})
        self.statusBar().showMessage(f"🔍 Servidor encontrado: {url}")

        # Conectar automaticamente ao primeiro servidor encontrado
        if not self.webhook_url:
            self.connect_to_webhook(url)

    def on_discovery_status(self, status: str):
        """Atualiza status da descoberta"""
        self.statusBar().showMessage(status)

    def on_discovery_finished(self):
        """Quando a descoberta termina"""
        if not self.webhook_url and self.available_servers:
            # Se nenhuma conexão foi estabelecida, tentar o primeiro servidor
            first_server = self.available_servers[0]
            self.connect_to_webhook(first_server["url"])
        elif not self.available_servers:
            self.statusBar().showMessage("❌ Nenhum webhook encontrado. Inicie o servidor webhook primeiro.")

    def connect_to_webhook(self, url: str):
        """Conecta a um webhook específico"""
        self.webhook_url = url
        self.setup_webhook_listener()
        self.contact_status.setText("Conectando...")
        self.statusBar().showMessage(f"🔗 Conectando a {url}")

    def setup_webhook_listener(self):
        """Configura listener do webhook"""
        if self.webhook_listener:
            self.webhook_listener.stop()
            self.webhook_listener.wait()

        if self.webhook_url:
            self.webhook_listener = WebhookListener(self.webhook_url)
            self.webhook_listener.message_received.connect(self.on_message_received)
            self.webhook_listener.status_received.connect(self.on_status_received)
            self.webhook_listener.connection_status.connect(self.on_connection_status)
            self.webhook_listener.new_chat_created.connect(self.on_new_chat_created)
            self.webhook_listener.start()

    def on_new_chat_created(self, chat_id: str, name: str, last_message: str):
        """Quando um novo chat é criado automaticamente"""
        self.add_chat_to_list(chat_id, name, last_message, unread_count=1)
        self.statusBar().showMessage(f"💬 Nova conversa: {name}", 3000)

    def setup_ui(self):
        """Configura interface principal"""
        self.setWindowTitle("Chat Moderno - WhatsApp Integration")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter para divisão responsiva
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ===== PAINEL ESQUERDO =====
        left_panel = self.create_left_panel()
        left_panel.setFixedWidth(350)

        # ===== PAINEL CENTRAL =====
        right_panel = self.create_right_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)

        # Status bar
        self.statusBar().showMessage("Iniciando...")

        # System tray
        self.setup_system_tray()

    def create_left_panel(self):
        """Cria painel esquerdo com lista de conversas"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border-right: 1px solid #E0E0E0;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ===== CABEÇALHO =====
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #1976D2, stop:1 #42A5F5);
                border: none;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)

        # Título
        title = QLabel("Conversas")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")

        # Botão configurações com menu
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(30, 30)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2);
                border: none;
                border-radius: 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.3);
            }
        """)

        # Menu de configurações
        settings_menu = QMenu()

        # Ação para mostrar servidores disponíveis
        servers_action = QAction("🔍 Servidores Disponíveis", self)
        servers_action.triggered.connect(self.show_servers_dialog)
        settings_menu.addAction(servers_action)

        # Ação para reconectar
        reconnect_action = QAction("🔄 Reconectar", self)
        reconnect_action.triggered.connect(self.reconnect_webhook)
        settings_menu.addAction(reconnect_action)

        settings_menu.addSeparator()

        # Ação para buscar novos servidores
        discover_action = QAction("🕵️ Buscar Servidores", self)
        discover_action.triggered.connect(self.discover_servers)
        settings_menu.addAction(discover_action)

        # Ação para configurações
        config_action = QAction("⚙️ Configurações", self)
        config_action.triggered.connect(self.show_settings)
        settings_menu.addAction(config_action)

        settings_btn.setMenu(settings_menu)
        settings_btn.clicked.connect(lambda: settings_btn.showMenu())

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(settings_btn)

        # ===== BUSCA =====
        search_container = QFrame()
        search_container.setFixedHeight(50)
        search_container.setStyleSheet("background-color: white; border: none;")

        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(15, 10, 15, 10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar conversas...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E0E0E0;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 11px;
                background-color: #F5F5F5;
            }
            QLineEdit:focus {
                border-color: #1976D2;
                background-color: white;
            }
        """)
        self.search_input.textChanged.connect(self.filter_chats)
        search_layout.addWidget(self.search_input)

        # ===== LISTA DE CONVERSAS =====
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: white;
                outline: none;
            }
            QListWidget::item {
                border: none;
                padding: 0px;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
            }
        """)
        self.chat_list.itemClicked.connect(self.on_chat_selected)

        # Adicionar conversas de exemplo
        self.populate_chat_list()

        layout.addWidget(header)
        layout.addWidget(search_container)
        layout.addWidget(self.chat_list)

        return panel

    def create_right_panel(self):
        """Cria painel direito com chat ativo"""
        panel = QFrame()
        panel.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ===== CABEÇALHO DO CHAT =====
        self.chat_header = self.create_chat_header()

        # ===== ÁREA DE MENSAGENS =====
        self.messages_area = self.create_messages_area()

        # ===== ÁREA DE INPUT =====
        self.input_area = self.create_input_area()

        layout.addWidget(self.chat_header)
        layout.addWidget(self.messages_area, 1)
        layout.addWidget(self.input_area)

        return panel

    def create_chat_header(self):
        """Cria cabeçalho do chat ativo"""
        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #1976D2, stop:1 #42A5F5);
                border: none;
            }
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # Avatar do contato
        self.contact_avatar = QLabel()
        self.contact_avatar.setFixedSize(50, 50)
        self.contact_avatar.setStyleSheet("""
            QLabel {
                border-radius: 25px;
                background-color: rgba(255,255,255,0.2);
                border: 2px solid rgba(255,255,255,0.3);
                font-size: 18px;
                font-weight: bold;
                color: white;
            }
        """)
        self.contact_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.contact_avatar.setText("💬")

        # Informações do contato
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.contact_name = QLabel("Selecione uma conversa")
        self.contact_name.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.contact_name.setStyleSheet("color: white;")

        self.contact_status = QLabel("Online")
        self.contact_status.setFont(QFont("Segoe UI", 9))
        self.contact_status.setStyleSheet("color: rgba(255,255,255,0.8);")

        info_layout.addWidget(self.contact_name)
        info_layout.addWidget(self.contact_status)

        # Botões de ação
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        call_btn = QPushButton("📞")
        video_btn = QPushButton("📹")
        menu_btn = QPushButton("⋮")

        for btn in [call_btn, video_btn, menu_btn]:
            btn.setFixedSize(40, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255,255,255,0.2);
                    border: none;
                    border-radius: 20px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.3);
                }
            """)

        actions_layout.addWidget(call_btn)
        actions_layout.addWidget(video_btn)
        actions_layout.addWidget(menu_btn)

        layout.addWidget(self.contact_avatar)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addLayout(actions_layout)

        return header

    def create_messages_area(self):
        """Cria área de mensagens"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F8F9FA;
            }
            QScrollBar:vertical {
                background-color: #F0F0F0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #BDBDBD;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9E9E9E;
            }
        """)

        # Container das mensagens
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()

        scroll_area.setWidget(self.messages_container)

        # Indicador de digitação
        self.typing_indicator = TypingIndicator()
        self.typing_indicator.hide()

        return scroll_area

    def create_input_area(self):
        """Cria área de input de mensagem"""
        container = QFrame()
        container.setFixedHeight(80)
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #E0E0E0;
            }
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # Botão anexar
        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(40, 40)
        attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
        """)
        attach_btn.clicked.connect(self.attach_file)

        # Input de texto
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Digite sua mensagem...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E0E0E0;
                border-radius: 25px;
                padding: 12px 20px;
                font-size: 11px;
                background-color: #F8F9FA;
            }
            QLineEdit:focus {
                border-color: #1976D2;
                background-color: white;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)

        # Botão emoji
        emoji_btn = QPushButton("😊")
        emoji_btn.setFixedSize(40, 40)
        emoji_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
        """)

        # Botão enviar
        self.send_btn = QPushButton("✈️")
        self.send_btn.setFixedSize(45, 45)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1976D2, stop:1 #42A5F5);
                border: none;
                border-radius: 22px;
                font-size: 16px;
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1565C0, stop:1 #1976D2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0D47A1, stop:1 #1565C0);
            }
        """)
        self.send_btn.clicked.connect(self.send_message)

        layout.addWidget(attach_btn)
        layout.addWidget(self.message_input, 1)
        layout.addWidget(emoji_btn)
        layout.addWidget(self.send_btn)

        return container

    def setup_webhook_listener(self):
        """Configura listener do webhook"""
        self.webhook_listener = WebhookListener(self.webhook_url)
        self.webhook_listener.message_received.connect(self.on_message_received)
        self.webhook_listener.status_received.connect(self.on_status_received)
        self.webhook_listener.connection_status.connect(self.on_connection_status)
        self.webhook_listener.start()

    def setup_system_tray(self):
        """Configura system tray"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon()
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))

            tray_menu = QMenu()
            show_action = QAction("Mostrar", self)
            show_action.triggered.connect(self.show)
            quit_action = QAction("Sair", self)
            quit_action.triggered.connect(self.close)

            tray_menu.addAction(show_action)
            tray_menu.addSeparator()
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

    def populate_chat_list(self):
        """Popula lista de conversas com dados de exemplo (apenas se vazia)"""
        # Só adicionar exemplos se não houver chats e nenhum webhook conectado
        if len(self.chats) == 0 and not self.webhook_url:
            sample_chats = [
                {
                    "id": "exemplo_chat_1",
                    "name": "💬 Chat de Exemplo",
                    "last_message": "Esta é uma conversa de exemplo. Conecte um webhook para ver conversas reais.",
                    "timestamp": "Demo",
                    "unread": 0
                }
            ]

            for chat in sample_chats:
                item = QListWidgetItem()
                chat_widget = ChatListItem(
                    chat["id"], chat["name"], chat["last_message"],
                    chat["timestamp"], chat["unread"]
                )

                item.setSizeHint(chat_widget.sizeHint())
                self.chat_list.addItem(item)
                self.chat_list.setItemWidget(item, chat_widget)

                # Armazenar conversa de exemplo
                self.chats[chat["id"]] = {
                    "name": chat["name"],
                    "messages": [
                        {
                            "text": "🎉 Bem-vindo ao Chat Moderno!",
                            "is_sent": False,
                            "timestamp": "Demo",
                            "sender_name": "Sistema",
                            "message_id": "demo_1"
                        },
                        {
                            "text": "Esta é uma interface moderna para WhatsApp Business API.",
                            "is_sent": False,
                            "timestamp": "Demo",
                            "sender_name": "Sistema",
                            "message_id": "demo_2"
                        },
                        {
                            "text": "Para começar, execute o webhook:\npython webhook_whatsapp.py",
                            "is_sent": False,
                            "timestamp": "Demo",
                            "sender_name": "Sistema",
                            "message_id": "demo_3"
                        },
                        {
                            "text": "As conversas reais aparecerão automaticamente aqui! 🚀",
                            "is_sent": False,
                            "timestamp": "Demo",
                            "sender_name": "Sistema",
                            "message_id": "demo_4"
                        }
                    ]
                }

    def on_chat_selected(self, item):
        """Quando uma conversa é selecionada"""
        widget = self.chat_list.itemWidget(item)
        if widget:
            self.current_chat_id = widget.chat_id
            self.contact_name.setText(widget.name)
            self.contact_avatar.setText(widget.name[:1].upper())
            self.load_chat_messages()

    def load_chat_messages(self):
        """Carrega mensagens da conversa atual"""
        # Limpar mensagens atuais
        for i in reversed(range(self.messages_layout.count())):
            child = self.messages_layout.itemAt(i).widget()
            if child and isinstance(child, MessageBubble):
                child.setParent(None)

        # Carregar mensagens da conversa
        if self.current_chat_id in self.chats:
            for msg in self.chats[self.current_chat_id]["messages"]:
                self.add_message_bubble(
                    msg["text"], msg["is_sent"], msg["timestamp"],
                    msg.get("sender_name", ""), msg.get("message_id", "")
                )

    def add_message_bubble(self, text: str, is_sent: bool = False,
                           timestamp: str = "", sender_name: str = "", message_id: str = ""):
        """Adiciona bolha de mensagem"""
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")

        bubble = MessageBubble(text, is_sent, timestamp, sender_name, "", message_id)

        # Inserir antes do stretch
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)

        # Scroll automático
        QTimer.singleShot(100, self.scroll_to_bottom)

        # Animação de entrada
        self.animate_message_entry(bubble)

    def animate_message_entry(self, bubble):
        """Anima entrada da mensagem"""
        bubble.setMaximumHeight(0)

        animation = QPropertyAnimation(bubble, b"maximumHeight")
        animation.setDuration(300)
        animation.setStartValue(0)
        animation.setEndValue(bubble.sizeHint().height())
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()

    def scroll_to_bottom(self):
        """Faz scroll até o final"""
        scroll_area = self.messages_area
        scroll_bar = scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def send_message(self):
        """Envia mensagem"""
        text = self.message_input.text().strip()
        if not text or not self.current_chat_id:
            return

        # Adicionar à interface
        self.add_message_bubble(text, is_sent=True)

        # Salvar na conversa
        if self.current_chat_id in self.chats:
            self.chats[self.current_chat_id]["messages"].append({
                "text": text,
                "is_sent": True,
                "timestamp": datetime.now().strftime("%H:%M"),
                "message_id": f"msg_{int(time.time())}"
            })

        # Limpar input
        self.message_input.clear()

        # Enviar via webhook (implementar conforme API)
        self.send_via_webhook(text)

        # Simular resposta automática (remover em produção)
        QTimer.singleShot(2000, lambda: self.simulate_typing())
        QTimer.singleShot(4000, lambda: self.simulate_response())

    def send_via_webhook(self, message: str):
        """Envia mensagem via webhook"""
        try:
            payload = {
                "to": self.current_chat_id,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }

            response = requests.post(
                f"{self.webhook_url}/send",
                json=payload,
                timeout=5
            )

            if response.status_code == 200:
                self.statusBar().showMessage("Mensagem enviada", 2000)
            else:
                self.statusBar().showMessage("Erro ao enviar mensagem", 3000)

        except Exception as e:
            self.statusBar().showMessage(f"Erro: {str(e)}", 3000)

    def simulate_typing(self):
        """Simula indicador de digitação"""
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, self.typing_indicator)
        self.typing_indicator.show()
        self.typing_indicator.start_animation()
        self.scroll_to_bottom()

    def simulate_response(self):
        """Simula resposta automática"""
        self.typing_indicator.stop_animation()
        self.typing_indicator.hide()
        self.typing_indicator.setParent(None)

        responses = [
            "Oi! Como você está?", "Que legal!", "Entendi 👍",
            "Vou verificar isso", "Obrigado pela mensagem!"
        ]

        response = responses[int(time.time()) % len(responses)]
        sender_name = self.chats[self.current_chat_id]["name"] if self.current_chat_id in self.chats else "Contato"

        self.add_message_bubble(response, is_sent=False, sender_name=sender_name)

        # Salvar resposta
        if self.current_chat_id in self.chats:
            self.chats[self.current_chat_id]["messages"].append({
                "text": response,
                "is_sent": False,
                "timestamp": datetime.now().strftime("%H:%M"),
                "sender_name": sender_name,
                "message_id": f"msg_{int(time.time())}_recv"
            })

    def on_message_received(self, data: dict):
        """Processa mensagem recebida do webhook"""
        try:
            chat_id = data.get("chat", {}).get("id", "")
            sender = data.get("sender", {})
            sender_name = sender.get("pushName", "Contato")
            sender_id = sender.get("id", "")
            content = data.get("msgContent", {})
            message_text = content.get("conversation", "")
            is_from_me = data.get("fromMe", False)

            if not chat_id:
                chat_id = sender_id  # Usar ID do remetente como fallback

            if chat_id and message_text:
                # Verificar se é uma mensagem enviada por mim
                if is_from_me:
                    # Ignorar mensagens enviadas por mim (já foram processadas localmente)
                    return

                # Criar conversa se não existir
                if chat_id not in self.chats:
                    print(f"🆕 Criando nova conversa para {sender_name} ({chat_id})")
                    self.chats[chat_id] = {
                        "name": sender_name or f"Contato {chat_id[-4:]}",
                        "messages": []
                    }

                    # Adicionar à lista de conversas
                    self.add_chat_to_list(
                        chat_id,
                        self.chats[chat_id]["name"],
                        message_text,
                        unread_count=1
                    )

                    # Emitir sinal de novo chat criado
                    self.webhook_listener.new_chat_created.emit(
                        chat_id,
                        self.chats[chat_id]["name"],
                        message_text
                    )
                else:
                    # Atualizar nome se mudou
                    if sender_name and sender_name != self.chats[chat_id]["name"]:
                        self.chats[chat_id]["name"] = sender_name
                        self.update_chat_in_list(chat_id, sender_name, message_text)

                # Adicionar mensagem se for o chat atual
                if self.current_chat_id == chat_id:
                    self.add_message_bubble(
                        message_text,
                        is_sent=False,
                        sender_name=sender_name
                    )

                    # Reproduzir som de notificação
                    self.play_notification_sound()
                else:
                    # Atualizar contador de mensagens não lidas
                    self.update_unread_count(chat_id, 1)

                # Salvar mensagem
                self.chats[chat_id]["messages"].append({
                    "text": message_text,
                    "is_sent": False,
                    "timestamp": datetime.now().strftime("%H:%M"),
                    "sender_name": sender_name,
                    "message_id": data.get("messageId", "")
                })

                # Atualizar status bar
                self.statusBar().showMessage(f"📨 Nova mensagem de {sender_name}", 3000)

                # Mostrar notificação desktop se não estiver focado
                if not self.isActiveWindow():
                    self.show_desktop_notification(
                        f"Nova mensagem - {sender_name}",
                        message_text[:50] + "..." if len(message_text) > 50 else message_text
                    )

        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
            self.statusBar().showMessage(f"❌ Erro ao processar mensagem: {e}", 5000)

    def update_chat_in_list(self, chat_id: str, name: str, last_message: str):
        """Atualiza chat existente na lista"""
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            widget = self.chat_list.itemWidget(item)
            if widget and hasattr(widget, 'chat_id') and widget.chat_id == chat_id:
                # Atualizar widget existente
                widget.name = name
                widget.last_message = last_message
                widget.timestamp = datetime.now().strftime("%H:%M")

                # Recriar o widget (método simples de atualização)
                new_widget = ChatListItem(chat_id, name, last_message, widget.timestamp, widget.unread_count)
                item.setSizeHint(new_widget.sizeHint())
                self.chat_list.setItemWidget(item, new_widget)
                break

    def update_unread_count(self, chat_id: str, increment: int = 1):
        """Atualiza contador de mensagens não lidas"""
        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            widget = self.chat_list.itemWidget(item)
            if widget and hasattr(widget, 'chat_id') and widget.chat_id == chat_id:
                widget.unread_count += increment

                # Recriar widget com novo contador
                new_widget = ChatListItem(
                    chat_id, widget.name, widget.last_message,
                    widget.timestamp, widget.unread_count
                )
                item.setSizeHint(new_widget.sizeHint())
                self.chat_list.setItemWidget(item, new_widget)
                break

    def play_notification_sound(self):
        """Reproduz som de notificação"""
        try:
            # Para Windows
            import winsound
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except ImportError:
            try:
                # Para Linux/Mac
                import os
                os.system("echo -e '\a'")
            except:
                pass

    def show_desktop_notification(self, title: str, message: str):
        """Mostra notificação desktop"""
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.showMessage(
                    title,
                    message,
                    QSystemTrayIcon.MessageIcon.Information,
                    3000  # 3 segundos
                )
        except:
            pass

    def on_status_received(self, data: dict):
        """Processa status recebido do webhook"""
        status = data.get("status", "")
        message_id = data.get("messageId", "")

        if status == "DELIVERY":
            # Atualizar status de entrega
            self.update_message_status(message_id, "delivered")

    def on_connection_status(self, connected: bool, message: str):
        """Atualiza status da conexão"""
        if connected:
            self.statusBar().showMessage(f"✅ {message}")
            self.contact_status.setText("Online")
        else:
            self.statusBar().showMessage(f"❌ {message}")
            self.contact_status.setText("Desconectado")

    def add_chat_to_list(self, chat_id: str, name: str, last_message: str):
        """Adiciona nova conversa à lista"""
        item = QListWidgetItem()
        chat_widget = ChatListItem(
            chat_id, name, last_message,
            datetime.now().strftime("%H:%M"), 1
        )

        item.setSizeHint(chat_widget.sizeHint())
        self.chat_list.insertItem(0, item)  # Adicionar no topo
        self.chat_list.setItemWidget(item, chat_widget)

    def update_message_status(self, message_id: str, status: str):
        """Atualiza status da mensagem"""
        # Implementar atualização visual do status
        pass

    def filter_chats(self, text: str):
        """Filtra conversas baseado no texto de busca"""
        text = text.lower().strip()

        for i in range(self.chat_list.count()):
            item = self.chat_list.item(i)
            widget = self.chat_list.itemWidget(item)

            if widget and hasattr(widget, 'name'):
                # Verificar se o nome ou última mensagem contém o texto
                name_match = text in widget.name.lower()
                message_match = text in widget.last_message.lower()

                # Mostrar/esconder item baseado na busca
                if text == "" or name_match or message_match:
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    def attach_file(self):
        """Anexar arquivo"""
        if not self.current_chat_id:
            self.statusBar().showMessage("❌ Selecione uma conversa primeiro", 3000)
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo",
            "", "Todos os Arquivos (*)"
        )

        if file_path:
            file_name = Path(file_path).name
            self.add_message_bubble(f"📎 {file_name}", is_sent=True)
            self.statusBar().showMessage(f"📎 Arquivo anexado: {file_name}", 3000)

    def show_servers_dialog(self):
        """Mostra diálogo com servidores disponíveis"""
        if not self.available_servers:
            QMessageBox.information(
                self, "Servidores",
                "❌ Nenhum servidor encontrado.\n\nInicie o webhook primeiro:\npython webhook_whatsapp.py"
            )
            return

        dialog = QMessageBox()
        dialog.setWindowTitle("Servidores Webhook Disponíveis")
        dialog.setIcon(QMessageBox.Icon.Information)

        server_info = []
        for i, server in enumerate(self.available_servers):
            status = "🟢 CONECTADO" if server["url"] == self.webhook_url else "⚪ Disponível"
            server_info.append(f"{i + 1}. {server['url']}\n   {server['description']}\n   Status: {status}")

        dialog.setText("🔍 Servidores Encontrados:\n\n" + "\n\n".join(server_info))

        # Botões para conectar
        if len(self.available_servers) > 1:
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
            dialog.addButton("🔄 Trocar Servidor", QMessageBox.ButtonRole.ActionRole)
        else:
            dialog.setStandardButtons(QMessageBox.StandardButton.Ok)

        result = dialog.exec()

        if result == 1:  # Trocar servidor
            self.choose_server_dialog()

    def choose_server_dialog(self):
        """Diálogo para escolher servidor"""
        from PyQt6.QtWidgets import QInputDialog

        server_names = [f"{s['url']} - {s['description']}" for s in self.available_servers]

        item, ok = QInputDialog.getItem(
            self, "Escolher Servidor",
            "🔗 Selecione o servidor webhook:",
            server_names, 0, False
        )

        if ok and item:
            # Encontrar servidor selecionado
            for server in self.available_servers:
                if item.startswith(server['url']):
                    self.connect_to_webhook(server['url'])
                    break

    def reconnect_webhook(self):
        """Reconecta ao webhook atual"""
        if self.webhook_url:
            self.statusBar().showMessage("🔄 Reconectando...")
            self.setup_webhook_listener()
        else:
            self.discover_servers()

    def on_connection_status(self, connected: bool, message: str):
        """Atualiza status da conexão"""
        if connected:
            self.statusBar().showMessage(f"✅ {message}")
            self.contact_status.setText("🟢 Online")
        else:
            self.statusBar().showMessage(f"❌ {message}")
            self.contact_status.setText("🔴 Desconectado")

    def show_settings(self):
        """Mostra configurações"""
        dialog = QMessageBox()
        dialog.setWindowTitle("Configurações do Chat")
        dialog.setIcon(QMessageBox.Icon.Information)

        settings_text = f"""⚙️ CONFIGURAÇÕES ATUAIS

🔗 Webhook URL: {self.webhook_url or 'Não conectado'}
📱 Conversas ativas: {len(self.chats)}
🔍 Servidores encontrados: {len(self.available_servers)}

💡 RECURSOS DISPONÍVEIS:
• ✅ Detecção automática de servidores
• ✅ Criação automática de conversas  
• ✅ Notificações em tempo real
• ✅ Interface responsiva
• ✅ Múltiplos formatos de webhook

🚀 COMO USAR:
1. Execute o webhook: python webhook_whatsapp.py
2. O chat se conectará automaticamente
3. Mensagens do WhatsApp aparecerão aqui
4. Responda normalmente pela interface

🔧 SOLUÇÃO DE PROBLEMAS:
• Use 'Buscar Servidores' se não conectar
• Verifique se o webhook está rodando
• Teste a URL no navegador: {self.webhook_url or 'N/A'}/status
"""

        dialog.setText(settings_text)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()

    def closeEvent(self, event):
        """Evento de fechamento"""
        if self.webhook_listener:
            self.webhook_listener.stop()
            self.webhook_listener.wait()

        if self.server_discovery:
            self.server_discovery.stop()
            self.server_discovery.wait()

    def apply_theme(self):
        """Aplica tema à aplicação"""
        if self.dark_mode:
            # Tema escuro (implementar futuramente)
            pass
        else:
            # Tema claro (já implementado)
            pass

    def on_status_received(self, data: dict):
        """Processa status recebido do webhook"""
        status = data.get("status", "")
        message_id = data.get("messageId", "")

        if status == "DELIVERY":
            # Atualizar status de entrega
            self.update_message_status(message_id, "delivered")

    def update_message_status(self, message_id: str, status: str):
        """Atualiza status da mensagem"""
        # Implementar atualização visual do status
        for i in reversed(range(self.messages_layout.count())):
            widget = self.messages_layout.itemAt(i).widget()
            if isinstance(widget, MessageBubble) and hasattr(widget, 'message_id'):
                if widget.message_id == message_id:
                    widget.mark_as_read()
                    break


def main():
    """Função principal"""
    app = QApplication(sys.argv)
    app.setApplicationName("Chat Moderno - WhatsApp Integration")
    app.setApplicationVersion("2.0")

    # Configurar fonte padrão
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    print("🚀 CHAT MODERNO - WhatsApp Integration v2.0")
    print("=" * 60)
    print("✨ Recursos:")
    print("• 🔍 Detecção automática de servidores webhook")
    print("• 💬 Criação automática de conversas")
    print("• 🔔 Notificações em tempo real")
    print("• 🎨 Interface moderna e responsiva")
    print("• 🔄 Reconexão automática")
    print("=" * 60)

    # Verificar dependências críticas
    try:
        import requests
        print("✅ Requests disponível")
    except ImportError:
        print("❌ Módulo 'requests' não encontrado!")
        print("💡 Execute: pip install requests")
        return 1

    # Criar e mostrar interface
    try:
        window = ModernChatInterface()
        window.show()

        print("🖥️ Interface iniciada com sucesso!")
        print("🔍 Buscando servidores webhook...")
        print("💡 Para iniciar o webhook, execute em outro terminal:")
        print("   python webhook_whatsapp.py")
        print("=" * 60)

        # Executar aplicação
        return app.exec()

    except Exception as e:
        print(f"❌ Erro ao iniciar interface: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())