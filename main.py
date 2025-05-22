#!/usr/bin/env python3
"""
WhatsApp Clone v2.0 - Integração W-API
Aplicativo moderno de WhatsApp com integração real à W-API

Autor: Assistente Claude
Versão: 2.0
Data: 2025
"""

import sys
import json
import requests
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QPushButton, QLabel,
    QFrame, QScrollArea, QSplitter, QDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QMenuBar, QMenu, QStatusBar,
    QProgressBar, QComboBox, QSpinBox, QCheckBox, QTabWidget,
    QTextBrowser
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QSettings
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QAction


# ============================================================================
# GERENCIADOR DE API
# ============================================================================

class APIManager(QObject):
    """Gerenciador centralizado para comunicação com a W-API"""

    message_received = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.settings = QSettings("WhatsAppClone", "API")
        self.client = None
        self.load_settings()

    def configure(self, base_url, token, instance_id):
        """Configura a API com os parâmetros fornecidos"""
        # Salvar configurações
        self.settings.setValue("base_url", base_url)
        self.settings.setValue("token", token)
        self.settings.setValue("instance_id", instance_id)

        # Criar cliente W-API
        from api_client import WAPIClient
        self.client = WAPIClient(base_url, token, instance_id)

    def load_settings(self):
        """Carrega configurações salvas"""
        base_url = self.settings.value("base_url", "")
        token = self.settings.value("token", "")
        instance_id = self.settings.value("instance_id", "")

        if token and instance_id:
            from api_client import WAPIClient
            self.client = WAPIClient(base_url, token, instance_id)

    @property
    def token(self):
        """Retorna o token atual"""
        return self.settings.value("token", "")

    def get_instance_status(self):
        """Obtém status da instância"""
        if not self.client:
            return False, {'error': 'Cliente não configurado'}
        return self.client.get_instance_status()

    def get_instance_qr_code(self):
        """Obtém QR Code da instância"""
        if not self.client:
            return False, {'error': 'Cliente não configurado'}
        return self.client.get_instance_qr_code()

    def send_text_message(self, phone_number, message):
        """Envia mensagem de texto"""
        if not self.client:
            return False, {'error': 'Cliente não configurado'}
        return self.client.send_text_message(phone_number, message)

    def get_profile_info(self):
        """Obtém informações do perfil"""
        if not self.client:
            return False, {'error': 'Cliente não configurado'}
        return self.client.get_profile_info()

    def get_chats(self):
        """Obtém lista de chats"""
        if not self.client:
            return False, []
        return self.client.get_chats()


# ============================================================================
# DIALOG DE QR CODE
# ============================================================================

class QRCodeDialog(QDialog):
    """Dialog para exibir e gerenciar QR Code do WhatsApp"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("QR Code - Conectar WhatsApp")
        self.setModal(True)
        self.setFixedSize(500, 600)
        self.api_manager = None
        self.setup_ui()

    def setup_ui(self):
        """Configura a interface do dialog"""
        layout = QVBoxLayout()

        # Título
        title = QLabel("📱 Conectar WhatsApp")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #E4E6EA; margin: 10px;")

        # Instruções
        instructions = QLabel("""
        <div style='text-align: center; color: #8696A0; font-size: 13px;'>
        <p>1. Abra o WhatsApp no seu celular</p>
        <p>2. Vá em <b>Menu → Dispositivos conectados</b></p>
        <p>3. Toque em <b>"Conectar um dispositivo"</b></p>
        <p>4. Escaneie o QR Code abaixo</p>
        </div>
        """)
        instructions.setWordWrap(True)

        # Label para QR Code
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(400, 400)
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setStyleSheet("""
            QLabel {
                border: 2px solid #3C4043;
                border-radius: 10px;
                background-color: #2A3942;
                color: #8696A0;
                font-size: 14px;
            }
        """)
        self.qr_label.setText("Carregando QR Code...")

        # Status
        self.status_label = QLabel("Preparando...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #8696A0; font-size: 12px; margin: 10px;")

        # Botões
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("🔄 Atualizar QR")
        self.refresh_button.clicked.connect(self.refresh_qr_code)

        self.close_button = QPushButton("Fechar")
        self.close_button.clicked.connect(self.accept)

        # Timer para verificar status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_connection_status)

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.close_button)

        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addWidget(self.qr_label)
        layout.addWidget(self.status_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.apply_styles()

    def apply_styles(self):
        """Aplica estilos CSS ao dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #202C33;
                color: #E4E6EA;
            }
            QPushButton {
                background-color: #00D4AA;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00BFA5;
            }
            QPushButton:pressed {
                background-color: #00A693;
            }
        """)

    def set_api_manager(self, api_manager):
        """Define o gerenciador de API"""
        self.api_manager = api_manager

    def show_qr_code(self):
        """Exibe o dialog e carrega o QR Code"""
        if not self.api_manager:
            QMessageBox.warning(self, "Erro", "API não configurada")
            return

        self.show()
        self.load_qr_code()

        # Iniciar timer para verificar status a cada 3 segundos
        self.status_timer.start(3000)

    def load_qr_code(self):
        """Carrega o QR Code da API"""
        if not self.api_manager:
            return

        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Carregando...")
        self.status_label.setText("Gerando QR Code...")

        try:
            success, qr_data = self.api_manager.get_instance_qr_code()

            if success:
                if qr_data.get('type') == 'base64':
                    # QR Code em base64
                    self.display_base64_qr(qr_data.get('qrcode', ''))
                    self.status_label.setText("✅ QR Code gerado. Escaneie com seu celular.")

                elif qr_data.get('type') == 'binary':
                    # QR Code como imagem binária
                    self.display_binary_qr(qr_data.get('qrcode', b''))
                    self.status_label.setText("✅ QR Code gerado. Escaneie com seu celular.")

                else:
                    self.status_label.setText("❌ Formato de QR Code não suportado")
                    self.qr_label.setText("Formato não suportado")
            else:
                error_msg = qr_data.get('error', 'Erro desconhecido')
                self.status_label.setText(f"❌ Erro: {error_msg}")
                self.qr_label.setText(f"Erro ao gerar QR Code:\n{error_msg}")

        except Exception as e:
            self.status_label.setText(f"❌ Erro: {str(e)}")
            self.qr_label.setText(f"Erro inesperado:\n{str(e)}")

        finally:
            self.refresh_button.setEnabled(True)
            self.refresh_button.setText("🔄 Atualizar QR")

    def display_base64_qr(self, base64_data: str):
        """Exibe QR Code a partir de dados base64"""
        try:
            import base64
            from io import BytesIO

            # Remover prefixo data:image se existir
            if base64_data.startswith('data:image'):
                base64_data = base64_data.split(',')[1]

            # Decodificar base64
            image_data = base64.b64decode(base64_data)

            # Criar pixmap
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)

            # Redimensionar mantendo proporção
            pixmap = pixmap.scaled(380, 380, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)

            self.qr_label.setPixmap(pixmap)

        except Exception as e:
            self.qr_label.setText(f"Erro ao exibir QR Code:\n{str(e)}")

    def display_binary_qr(self, binary_data: bytes):
        """Exibe QR Code a partir de dados binários"""
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(binary_data)

            # Redimensionar mantendo proporção
            pixmap = pixmap.scaled(380, 380, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)

            self.qr_label.setPixmap(pixmap)

        except Exception as e:
            self.qr_label.setText(f"Erro ao exibir QR Code:\n{str(e)}")

    def refresh_qr_code(self):
        """Atualiza o QR Code"""
        self.load_qr_code()

    def check_connection_status(self):
        """Verifica se o WhatsApp foi conectado"""
        if not self.api_manager:
            return

        try:
            success, status_data = self.api_manager.get_instance_status()

            if success and status_data.get('connected'):
                # WhatsApp conectado!
                self.status_timer.stop()
                self.status_label.setText("✅ WhatsApp conectado com sucesso!")

                # Exibir informações da conexão
                phone = status_data.get('phone_number', '')
                name = status_data.get('pushname', '')

                if phone or name:
                    info_text = f"📱 {name} ({phone})" if name else f"📱 {phone}"
                    self.status_label.setText(f"✅ Conectado: {info_text}")

                # Fechar dialog após 2 segundos
                QTimer.singleShot(2000, self.accept)

        except Exception as e:
            # Ignorar erros na verificação de status
            pass

    def closeEvent(self, event):
        """Limpar timer ao fechar"""
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        super().closeEvent(event)


# ============================================================================
# DIALOG DE CONFIGURAÇÃO
# ============================================================================

class ConfigDialog(QDialog):
    """Dialog para configuração da API W-API"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações da API")
        self.setModal(True)
        self.setFixedSize(500, 400)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Configura a interface do dialog"""
        layout = QVBoxLayout()

        # Tabs
        tab_widget = QTabWidget()

        # Tab de Configuração Básica
        basic_tab = QWidget()
        basic_layout = QFormLayout()

        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.w-api.app/v1")
        self.base_url_input.setText("https://api.w-api.app/v1")  # URL padrão

        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Seu token da W-API")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.instance_input = QLineEdit()
        self.instance_input.setPlaceholderText("ID da instância")

        basic_layout.addRow("URL Base da API:", self.base_url_input)
        basic_layout.addRow("Token:", self.token_input)
        basic_layout.addRow("ID da Instância:", self.instance_input)

        # Botão de teste
        self.test_button = QPushButton("Testar Conexão")
        self.test_button.clicked.connect(self.test_connection)
        basic_layout.addRow("", self.test_button)

        # Status da conexão
        self.status_label = QLabel("Não testado")
        self.status_label.setStyleSheet("color: #8696A0;")
        basic_layout.addRow("Status:", self.status_label)

        basic_tab.setLayout(basic_layout)
        tab_widget.addTab(basic_tab, "Configuração")

        # Tab de Webhook
        webhook_tab = QWidget()
        webhook_layout = QFormLayout()

        self.webhook_url_input = QLineEdit()
        self.webhook_url_input.setPlaceholderText("https://seu-servidor.com/webhook")

        self.webhook_enabled = QCheckBox("Ativar Webhook")

        webhook_layout.addRow("URL do Webhook:", self.webhook_url_input)
        webhook_layout.addRow("", self.webhook_enabled)

        webhook_tab.setLayout(webhook_layout)
        tab_widget.addTab(webhook_tab, "Webhook")

        # Tab de Informações
        info_tab = QWidget()
        info_layout = QVBoxLayout()

        info_text = QTextBrowser()
        info_text.setHtml("""
        <h3>Como Configurar W-API</h3>
        <p><b>1. URL Base:</b> https://api.w-api.app/v1 (padrão)</p>
        <p><b>2. Token:</b> Token de autorização da sua conta W-API</p>
        <p><b>3. ID da Instância:</b> ID único da sua instância WhatsApp</p>

        <h3>Endpoints W-API Utilizados</h3>
        <ul>
            <li><b>Status:</b> GET /instance/status-instance</li>
            <li><b>QR Code:</b> GET /instance/qr-code</li>
            <li><b>Enviar:</b> POST /message/send-text</li>
            <li><b>Chats:</b> GET /message/get-chats</li>
            <li><b>Webhook:</b> POST /webhook</li>
        </ul>

        <h3>Exemplo de Configuração</h3>
        <pre>URL Base: https://api.w-api.app/v1
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Instance ID: 123456789</pre>

        <h3>Como Obter Credenciais</h3>
        <p>1. Acesse <a href="https://w-api.app">w-api.app</a></p>
        <p>2. Crie uma conta ou faça login</p>
        <p>3. Crie uma nova instância</p>
        <p>4. Copie o Token e Instance ID</p>
        """)

        info_layout.addWidget(info_text)
        info_tab.setLayout(info_layout)
        tab_widget.addTab(info_tab, "Ajuda")

        layout.addWidget(tab_widget)

        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)
        self.setLayout(layout)
        self.apply_styles()

    def apply_styles(self):
        """Aplica estilos CSS ao dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #202C33;
                color: #E4E6EA;
            }
            QLineEdit {
                background-color: #2A3942;
                border: 1px solid #3C4043;
                border-radius: 5px;
                padding: 8px;
                color: #FFFFFF;
            }
            QLineEdit::placeholder {
                color: #8696A0;
            }
            QPushButton {
                background-color: #00D4AA;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00BFA5;
            }
            QTabWidget::pane {
                border: 1px solid #3C4043;
                background-color: #202C33;
                color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #2A3942;
                color: #FFFFFF;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #00D4AA;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QFormLayout QLabel {
                color: #FFFFFF;
            }
            QTextBrowser {
                background-color: #2A3942;
                color: #FFFFFF;
                border: 1px solid #3C4043;
                border-radius: 5px;
            }
            QCheckBox {
                color: #FFFFFF;
            }
            QCheckBox::indicator {
                background-color: #2A3942;
                border: 1px solid #3C4043;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #00D4AA;
                border: 1px solid #00D4AA;
            }
        """)

    def load_settings(self):
        """Carrega configurações salvas"""
        settings = QSettings("WhatsAppClone", "API")
        self.base_url_input.setText(settings.value("base_url", "https://api.w-api.app/v1"))
        self.token_input.setText(settings.value("token", ""))
        self.instance_input.setText(settings.value("instance_id", ""))
        self.webhook_url_input.setText(settings.value("webhook_url", ""))
        self.webhook_enabled.setChecked(settings.value("webhook_enabled", False, type=bool))

    def save_settings(self):
        """Salva as configurações"""
        settings = QSettings("WhatsAppClone", "API")
        settings.setValue("base_url", self.base_url_input.text())
        settings.setValue("token", self.token_input.text())
        settings.setValue("instance_id", self.instance_input.text())
        settings.setValue("webhook_url", self.webhook_url_input.text())
        settings.setValue("webhook_enabled", self.webhook_enabled.isChecked())

    def test_connection(self):
        """Testa a conexão com a API"""
        self.test_button.setText("Testando...")
        self.test_button.setEnabled(False)
        self.status_label.setText("Testando conexão...")
        self.status_label.setStyleSheet("color: #FFA500;")

        # Criar instância temporária do cliente W-API para teste
        try:
            from api_client import WAPIClient
            test_client = WAPIClient(
                self.base_url_input.text().strip(),
                self.token_input.text().strip(),
                self.instance_input.text().strip()
            )

            success, result = test_client.get_instance_status()

            if success:
                connected = result.get('connected', False)
                phone = result.get('phone_number', '')

                if connected:
                    status_msg = f"✅ API Conectada - WhatsApp Ativo"
                    if phone:
                        status_msg += f" ({phone})"
                    self.status_label.setText(status_msg)
                    self.status_label.setStyleSheet("color: #00D4AA;")
                else:
                    self.status_label.setText("⚠️ API OK - WhatsApp Desconectado (use QR Code)")
                    self.status_label.setStyleSheet("color: #FFA500;")
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                self.status_label.setText(f"❌ {error_msg}")
                self.status_label.setStyleSheet("color: #FF6B6B;")

        except Exception as e:
            self.status_label.setText(f"❌ Erro: {str(e)}")
            self.status_label.setStyleSheet("color: #FF6B6B;")

        finally:
            self.test_button.setText("Testar Conexão")
            self.test_button.setEnabled(True)

    def get_config(self):
        """Retorna as configurações"""
        return {
            'base_url': self.base_url_input.text(),
            'token': self.token_input.text(),
            'instance_id': self.instance_input.text(),
            'webhook_url': self.webhook_url_input.text(),
            'webhook_enabled': self.webhook_enabled.isChecked()
        }


# ============================================================================
# WIDGETS DE INTERFACE
# ============================================================================

class ChatListItem(QWidget):
    """Widget para item da lista de chats"""

    def __init__(self, name, last_message, time, unread_count=0, phone_number=""):
        super().__init__()
        self.name = name
        self.phone_number = phone_number
        self.setup_ui(name, last_message, time, unread_count)

    def setup_ui(self, name, last_message, time, unread_count):
        """Configura a interface do widget"""
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)

        # Avatar (círculo colorido com inicial)
        avatar = QLabel()
        avatar.setFixedSize(50, 50)
        avatar.setStyleSheet("""
            QLabel {
                background-color: #00D4AA;
                border-radius: 25px;
                color: white;
                font-weight: bold;
                font-size: 18px;
            }
        """)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setText(name[0].upper())

        # Informações do contato
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        # Nome e horário
        top_layout = QHBoxLayout()
        name_label = QLabel(name)
        name_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #E4E6EA;")

        time_label = QLabel(time)
        time_label.setFont(QFont("Segoe UI", 11))
        time_label.setStyleSheet("color: #8696A0;")

        top_layout.addWidget(name_label)
        top_layout.addStretch()
        top_layout.addWidget(time_label)

        # Última mensagem e contador
        bottom_layout = QHBoxLayout()
        message_label = QLabel(last_message)
        message_label.setFont(QFont("Segoe UI", 12))
        message_label.setStyleSheet("color: #8696A0;")

        if unread_count > 0:
            unread_label = QLabel(str(unread_count))
            unread_label.setFixedSize(20, 20)
            unread_label.setStyleSheet("""
                QLabel {
                    background-color: #00D4AA;
                    border-radius: 10px;
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
            unread_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bottom_layout.addWidget(message_label)
            bottom_layout.addStretch()
            bottom_layout.addWidget(unread_label)
        else:
            bottom_layout.addWidget(message_label)

        info_layout.addLayout(top_layout)
        info_layout.addLayout(bottom_layout)

        layout.addWidget(avatar)
        layout.addLayout(info_layout)

        self.setLayout(layout)


class MessageBubble(QWidget):
    """Widget para bolha de mensagem"""

    def __init__(self, message, time, is_sent=False):
        super().__init__()
        self.setup_ui(message, time, is_sent)

    def setup_ui(self, message, time, is_sent):
        """Configura a interface do widget"""
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        bubble = QFrame()
        bubble_layout = QVBoxLayout()
        bubble_layout.setContentsMargins(15, 10, 15, 10)

        # Mensagem
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Segoe UI", 13))
        message_label.setStyleSheet("color: #E4E6EA;")

        # Horário
        time_label = QLabel(time)
        time_label.setFont(QFont("Segoe UI", 10))
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        time_label.setStyleSheet("color: #8696A0;")

        bubble_layout.addWidget(message_label)
        bubble_layout.addWidget(time_label)
        bubble.setLayout(bubble_layout)

        if is_sent:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #005C4B;
                    border-radius: 15px;
                    border-top-right-radius: 5px;
                }
            """)
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #202C33;
                    border-radius: 15px;
                    border-top-left-radius: 5px;
                }
            """)
            layout.addWidget(bubble)
            layout.addStretch()

        self.setLayout(layout)


# ============================================================================
# APLICAÇÃO PRINCIPAL
# ============================================================================

class WhatsAppClone(QMainWindow):
    """Aplicação principal do WhatsApp Clone"""

    def __init__(self):
        super().__init__()
        self.current_chat = None
        self.current_phone = None
        self.chats_data = self.load_sample_data()
        self.api_manager = APIManager()

        self.init_ui()
        self.setup_timer()
        self.setup_menu()
        self.setup_status_bar()
        self.load_chats()

    def init_ui(self):
        """Inicializa a interface principal"""
        self.setWindowTitle("WhatsApp Clone - Com Integração W-API")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Configurar painéis
        self.setup_sidebar()
        self.setup_chat_panel()

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.chat_panel)
        splitter.setSizes([400, 800])

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        # Aplicar tema escuro
        self.apply_dark_theme()

    def setup_sidebar(self):
        """Configura o painel lateral (lista de chats)"""
        self.sidebar = QWidget()
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(500)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Header da sidebar
        header = QWidget()
        header.setFixedHeight(70)
        header.setStyleSheet("background-color: #202C33; border-bottom: 1px solid #3C4043;")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("WhatsApp")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #E4E6EA;")

        # Botão de atualizar chats
        self.refresh_button = QPushButton("🔄")
        self.refresh_button.setFixedSize(40, 40)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2A3942;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #00D4AA;
            }
        """)
        self.refresh_button.clicked.connect(self.sync_chats_from_api)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_button)
        header.setLayout(header_layout)

        # Lista de chats
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                background-color: #111B21;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #2A3942;
                padding: 0px;
            }
            QListWidget::item:selected {
                background-color: #2A3942;
            }
            QListWidget::item:hover {
                background-color: #182229;
            }
        """)
        self.chat_list.itemClicked.connect(self.on_chat_selected)

        sidebar_layout.addWidget(header)
        sidebar_layout.addWidget(self.chat_list)
        self.sidebar.setLayout(sidebar_layout)

    def setup_chat_panel(self):
        """Configura o painel de chat"""
        self.chat_panel = QWidget()

        chat_layout = QVBoxLayout()
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Header do chat
        self.chat_header = QWidget()
        self.chat_header.setFixedHeight(70)
        self.chat_header.setStyleSheet("background-color: #202C33; border-bottom: 1px solid #3C4043;")

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.contact_name = QLabel("Selecione um chat")
        self.contact_name.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.contact_name.setStyleSheet("color: #E4E6EA;")

        self.contact_status = QLabel("")
        self.contact_status.setFont(QFont("Segoe UI", 12))
        self.contact_status.setStyleSheet("color: #8696A0;")

        contact_info = QVBoxLayout()
        contact_info.addWidget(self.contact_name)
        contact_info.addWidget(self.contact_status)

        header_layout.addLayout(contact_info)
        header_layout.addStretch()
        self.chat_header.setLayout(header_layout)

        # Área de mensagens
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #0B141A;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #202C33;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #8696A0;
                border-radius: 4px;
            }
        """)

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.addStretch()
        self.messages_widget.setLayout(self.messages_layout)
        self.messages_scroll.setWidget(self.messages_widget)

        # Input de mensagem
        self.setup_message_input()

        chat_layout.addWidget(self.chat_header)
        chat_layout.addWidget(self.messages_scroll)
        chat_layout.addWidget(self.input_container)

        self.chat_panel.setLayout(chat_layout)

    def setup_message_input(self):
        """Configura a área de input de mensagem"""
        self.input_container = QWidget()
        self.input_container.setFixedHeight(80)
        self.input_container.setStyleSheet("background-color: #202C33;")

        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(20, 15, 20, 15)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Digite uma mensagem...")
        self.message_input.setFont(QFont("Segoe UI", 13))
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #2A3942;
                border: none;
                border-radius: 25px;
                padding: 15px 20px;
                color: #E4E6EA;
            }
            QLineEdit::placeholder {
                color: #8696A0;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Enviar")
        self.send_button.setFixedSize(80, 50)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #00D4AA;
                border: none;
                border-radius: 25px;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #00BFA5;
            }
            QPushButton:pressed {
                background-color: #00A693;
            }
            QPushButton:disabled {
                background-color: #5A5A5A;
            }
        """)
        self.send_button.clicked.connect(self.send_message)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        self.input_container.setLayout(input_layout)

    def setup_menu(self):
        """Configura o menu superior"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #202C33;
                color: #E4E6EA;
                border-bottom: 1px solid #3C4043;
                padding: 5px;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #2A3942;
                border-radius: 3px;
            }
            QMenu {
                background-color: #202C33;
                color: #E4E6EA;
                border: 1px solid #3C4043;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #00D4AA;
            }
        """)

        # Menu API
        api_menu = menubar.addMenu("⚙️ API")

        config_action = QAction("Configurar API", self)
        config_action.triggered.connect(self.open_config_dialog)
        api_menu.addAction(config_action)

        api_menu.addSeparator()

        # Ação para QR Code
        qr_action = QAction("📱 Conectar WhatsApp (QR Code)", self)
        qr_action.triggered.connect(self.show_qr_code)
        api_menu.addAction(qr_action)

        test_connection_action = QAction("Testar Conexão", self)
        test_connection_action.triggered.connect(self.test_api_connection)
        api_menu.addAction(test_connection_action)

        get_profile_action = QAction("Ver Perfil", self)
        get_profile_action.triggered.connect(self.get_profile_info)
        api_menu.addAction(get_profile_action)

        sync_chats_action = QAction("Sincronizar Chats", self)
        sync_chats_action.triggered.connect(self.sync_chats_from_api)
        api_menu.addAction(sync_chats_action)

        # Menu Ajuda
        help_menu = menubar.addMenu("❓ Ajuda")

        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        """Configura a barra de status"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Label de status da API
        self.api_status_label = QLabel("API: Não configurada")
        self.api_status_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
        self.status_bar.addWidget(self.api_status_label)

        # Progress bar (oculta inicialmente)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #202C33;
                color: #E4E6EA;
                border-top: 1px solid #3C4043;
            }
        """)

        # Verificar status inicial da API
        self.check_api_status()

    def setup_timer(self):
        """Configura timers da aplicação"""
        # Timer para verificar status da API periodicamente
        self.api_timer = QTimer()
        self.api_timer.timeout.connect(self.check_api_status)
        self.api_timer.start(60000)  # 1 minuto

    def apply_dark_theme(self):
        """Aplica tema escuro à aplicação"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111B21;
            }
            QWidget {
                background-color: #111B21;
            }
        """)

    # ========================================================================
    # MÉTODOS DE DADOS
    # ========================================================================

    def load_sample_data(self):
        """Carrega dados de exemplo para demonstração"""
        return {
            "João Silva": {
                "last_message": "Oi, tudo bem?",
                "time": "14:30",
                "unread": 2,
                "status": "online",
                "phone": "5511999999999",
                "messages": [
                    {"text": "Oi, tudo bem?", "time": "14:25", "sent": False},
                    {"text": "Como foi o trabalho hoje?", "time": "14:30", "sent": False}
                ]
            },
            "Maria Santos": {
                "last_message": "Obrigada pela ajuda!",
                "time": "13:45",
                "unread": 0,
                "status": "online há 5 minutos",
                "phone": "5511888888888",
                "messages": [
                    {"text": "Conseguiu resolver o problema?", "time": "13:30", "sent": True},
                    {"text": "Sim! Obrigada pela ajuda!", "time": "13:45", "sent": False}
                ]
            },
            "Pedro Costa": {
                "last_message": "Até amanhã!",
                "time": "12:20",
                "unread": 0,
                "status": "online há 2 horas",
                "phone": "5511777777777",
                "messages": [
                    {"text": "Vamos nos falar amanhã então", "time": "12:15", "sent": True},
                    {"text": "Até amanhã!", "time": "12:20", "sent": False}
                ]
            },
            "Ana Oliveira": {
                "last_message": "Perfeito! 👍",
                "time": "11:30",
                "unread": 1,
                "status": "online há 30 minutos",
                "phone": "5511666666666",
                "messages": [
                    {"text": "A reunião vai ser às 15h", "time": "11:25", "sent": True},
                    {"text": "Perfeito! 👍", "time": "11:30", "sent": False}
                ]
            }
        }

    def load_chats(self):
        """Carrega lista de chats na interface"""
        self.chat_list.clear()
        for name, data in self.chats_data.items():
            item = QListWidgetItem()
            chat_widget = ChatListItem(name, data["last_message"], data["time"],
                                       data["unread"], data.get("phone", ""))
            item.setSizeHint(chat_widget.sizeHint())
            self.chat_list.addItem(item)
            self.chat_list.setItemWidget(item, chat_widget)

    # ========================================================================
    # MÉTODOS DE CHAT
    # ========================================================================

    def on_chat_selected(self, item):
        """Manipula seleção de chat"""
        widget = self.chat_list.itemWidget(item)
        self.current_chat = widget.name
        self.current_phone = widget.phone_number
        self.load_chat_messages()

        # Atualizar header
        chat_data = self.chats_data[self.current_chat]
        self.contact_name.setText(f"{self.current_chat} ({self.current_phone})")
        self.contact_status.setText(chat_data["status"])

        # Marcar como lido
        self.chats_data[self.current_chat]["unread"] = 0

    def load_chat_messages(self):
        """Carrega mensagens do chat atual"""
        # Limpar mensagens anteriores
        for i in reversed(range(self.messages_layout.count())):
            child = self.messages_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # Adicionar stretch no início
        self.messages_layout.addStretch()

        # Carregar mensagens do chat atual
        if self.current_chat in self.chats_data:
            messages = self.chats_data[self.current_chat]["messages"]
            for msg in messages:
                bubble = MessageBubble(msg["text"], msg["time"], msg["sent"])
                self.messages_layout.addWidget(bubble)

        # Scroll para o final
        QTimer.singleShot(100, self.scroll_to_bottom)

    def send_message(self):
        """Envia mensagem (via API ou offline)"""
        if not self.current_chat or not self.message_input.text().strip():
            return

        message_text = self.message_input.text().strip()
        current_time = datetime.now().strftime("%H:%M")

        # Verificar se deve usar API ou modo offline
        if self.api_manager.token and self.current_phone:
            self.send_message_via_api(message_text)
        else:
            self.send_message_offline(message_text, current_time)

    def send_message_via_api(self, message_text):
        """Envia mensagem através da API"""
        self.send_button.setEnabled(False)
        self.send_button.setText("Enviando...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminado

        # Tentar enviar via API
        success, response = self.api_manager.send_text_message(self.current_phone, message_text)

        current_time = datetime.now().strftime("%H:%M")

        if success:
            message_id = response.get('message_id', 'N/A')
            self.status_bar.showMessage(f"✅ Mensagem enviada via API (ID: {message_id})", 5000)

            # Adicionar mensagem aos dados locais
            self.add_message_to_chat(message_text, current_time, True)

            # Simular resposta após alguns segundos (opcional)
            QTimer.singleShot(3000, self.simulate_api_response)

        else:
            error_msg = response.get('error', 'Erro desconhecido')

            # Verificar se é erro de conexão
            if 'não está conectado' in error_msg or 'not connected' in error_msg.lower():
                self.status_bar.showMessage("⚠️ WhatsApp não conectado - Use o QR Code", 5000)

                # Perguntar se quer mostrar QR Code
                reply = QMessageBox.question(
                    self,
                    "WhatsApp Não Conectado",
                    "O WhatsApp não está conectado à instância.\n\nDeseja escanear o QR Code para conectar?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.show_qr_code()
            else:
                self.status_bar.showMessage(f"❌ Erro ao enviar: {error_msg}", 5000)

                # Perguntar se quer enviar no modo offline como fallback
                reply = QMessageBox.question(
                    self,
                    "Erro no Envio",
                    f"Falha ao enviar via API:\n{error_msg}\n\nDeseja enviar no modo offline?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.send_message_offline(message_text, current_time)

        self.send_button.setEnabled(True)
        self.send_button.setText("Enviar")
        self.progress_bar.setVisible(False)
        self.message_input.clear()

    def send_message_offline(self, message_text, current_time):
        """Envia mensagem no modo offline (simulado)"""
        self.add_message_to_chat(message_text, current_time, True)
        self.message_input.clear()
        self.status_bar.showMessage("📤 Mensagem enviada (modo offline)", 2000)

        # Simular resposta automática
        QTimer.singleShot(2000, self.simulate_response)

    def add_message_to_chat(self, message_text, time, is_sent):
        """Adiciona mensagem ao chat atual"""
        # Adicionar aos dados
        if self.current_chat not in self.chats_data:
            self.chats_data[self.current_chat] = {"messages": []}

        self.chats_data[self.current_chat]["messages"].append({
            "text": message_text,
            "time": time,
            "sent": is_sent
        })

        # Atualizar última mensagem
        self.chats_data[self.current_chat]["last_message"] = message_text
        self.chats_data[self.current_chat]["time"] = time

        # Adicionar bubble à interface
        bubble = MessageBubble(message_text, time, is_sent)
        self.messages_layout.addWidget(bubble)

        # Scroll para o final
        QTimer.singleShot(100, self.scroll_to_bottom)

    def simulate_response(self):
        """Simula resposta automática offline"""
        if not self.current_chat:
            return

        responses = [
            "Entendi!",
            "Ok, obrigado!",
            "Perfeito 👍",
            "Vou verificar",
            "Combinado!",
            "Até logo!"
        ]

        import random
        response = random.choice(responses)
        current_time = datetime.now().strftime("%H:%M")

        self.add_message_to_chat(response, current_time, False)

    def simulate_api_response(self):
        """Simula resposta através da API"""
        if not self.current_chat:
            return

        responses = [
            "Mensagem recebida via API! 📱",
            "Conectado através da W-API ✅",
            "Sistema funcionando perfeitamente!",
            "API integrada com sucesso 🚀"
        ]

        import random
        response = random.choice(responses)
        current_time = datetime.now().strftime("%H:%M")

        self.add_message_to_chat(response, current_time, False)
        self.status_bar.showMessage("📨 Nova mensagem recebida via API", 3000)

    def scroll_to_bottom(self):
        """Rola para o final da área de mensagens"""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ========================================================================
    # MÉTODOS DE API
    # ========================================================================

    def show_qr_code(self):
        """Exibe QR Code para conectar WhatsApp"""
        if not self.api_manager.token:
            QMessageBox.warning(self, "Aviso", "Configure a API primeiro!")
            return

        qr_dialog = QRCodeDialog(self)
        qr_dialog.set_api_manager(self.api_manager)
        qr_dialog.show_qr_code()

    def check_api_status(self):
        """Verifica o status da API"""
        if not self.api_manager.token:
            self.api_status_label.setText("API: Não configurada")
            self.api_status_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
            return

        success, message = self.api_manager.get_instance_status()
        if success:
            connected = message.get('connected', False)
            if connected:
                phone = message.get('phone_number', '')
                status_text = f"API: ✅ Conectado"
                if phone:
                    status_text += f" ({phone})"
                self.api_status_label.setText(status_text)
                self.api_status_label.setStyleSheet("color: #00D4AA; font-weight: bold;")
            else:
                self.api_status_label.setText("API: ⚠️ Não conectado ao WhatsApp")
                self.api_status_label.setStyleSheet("color: #FFA500; font-weight: bold;")
        else:
            error = message.get('error', 'Erro')
            self.api_status_label.setText(f"API: ❌ {error}")
            self.api_status_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")

    def open_config_dialog(self):
        """Abre dialog de configuração"""
        dialog = ConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_config()
            dialog.save_settings()

            # Atualizar API manager
            self.api_manager.configure(
                config['base_url'],
                config['token'],
                config['instance_id']
            )

            # Verificar status
            self.check_api_status()

            QMessageBox.information(self, "Configuração", "Configurações salvas com sucesso!")

    def test_api_connection(self):
        """Testa conexão com a API"""
        if not self.api_manager.token:
            QMessageBox.warning(self, "Aviso", "Configure a API primeiro!")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        success, data = self.api_manager.get_instance_status()

        self.progress_bar.setVisible(False)

        if success:
            connected = data.get('connected', False)
            phone = data.get('phone_number', '')
            status = data.get('status', 'unknown')

            if connected:
                info_msg = f"✅ API Conectada com Sucesso!\n\n"
                info_msg += f"📱 Status: WhatsApp Conectado\n"
                if phone:
                    info_msg += f"📞 Número: {phone}\n"
                info_msg += f"🔧 Status da Instância: {status}"
                QMessageBox.information(self, "Teste de Conexão", info_msg)
            else:
                warning_msg = f"⚠️ API Conectada, mas WhatsApp Desconectado\n\n"
                warning_msg += f"🔧 Status da Instância: {status}\n\n"
                warning_msg += "📱 Para conectar o WhatsApp:\n"
                warning_msg += "1. Use o menu 'API → Conectar WhatsApp (QR Code)'\n"
                warning_msg += "2. Escaneie o código com seu celular"

                QMessageBox.warning(self, "Teste de Conexão", warning_msg)
        else:
            error_msg = data.get('error', 'Erro desconhecido')
            QMessageBox.critical(self, "Teste de Conexão", f"❌ Falha na Conexão:\n\n{error_msg}")

    def get_profile_info(self):
        """Obtém informações do perfil"""
        if not self.api_manager.token:
            QMessageBox.warning(self, "Aviso", "Configure a API primeiro!")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        success, data = self.api_manager.get_profile_info()

        self.progress_bar.setVisible(False)

        if success:
            info = f"📱 Perfil WhatsApp\n\n"
            info += f"👤 Nome: {data.get('name', 'N/A')}\n"
            info += f"📞 Telefone: {data.get('phone', 'N/A')}\n"
            info += f"🔋 Bateria: {data.get('battery', 0)}%\n"
            info += f"💻 Plataforma: {data.get('platform', 'N/A')}\n"
            info += f"🆔 Instância: {data.get('instance_id', 'N/A')}\n"
            info += f"🔗 Conectado: {'✅ Sim' if data.get('connected') else '❌ Não'}"

            QMessageBox.information(self, "Informações do Perfil", info)
        else:
            error_msg = data.get('error', 'Erro desconhecido')
            if 'não conectada' in error_msg or 'not connected' in error_msg.lower():
                QMessageBox.warning(self, "Perfil",
                                    "WhatsApp não está conectado.\nUse o QR Code para conectar primeiro.")
            else:
                QMessageBox.warning(self, "Erro", f"Erro ao obter perfil:\n{error_msg}")

    def sync_chats_from_api(self):
        """Sincroniza chats da API"""
        if not self.api_manager.token:
            QMessageBox.warning(self, "Aviso", "Configure a API primeiro!")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.refresh_button.setText("⏳")

        success, data = self.api_manager.get_chats()

        if success and isinstance(data, list):
            # Processar chats da API
            api_chats = data[:10]  # Limitar a 10 chats

            for chat in api_chats:
                chat_id = chat.get('id', '')
                name = chat.get('name', chat.get('phone', 'Contato'))
                phone = chat.get('phone', '')
                last_msg = chat.get('last_message', 'Sem mensagens')
                timestamp = chat.get('timestamp', 0)

                # Converter timestamp para horário
                if timestamp:
                    time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                else:
                    time_str = "00:00"

                # Adicionar ou atualizar chat
                if name not in self.chats_data:
                    self.chats_data[name] = {
                        "last_message": last_msg,
                        "time": time_str,
                        "unread": 0,
                        "status": "via API",
                        "phone": phone,
                        "messages": []
                    }

            # Recarregar lista de chats
            self.load_chats()
            self.status_bar.showMessage(f"✅ {len(api_chats)} chats sincronizados", 3000)

        else:
            error_msg = "Erro na sincronização"
            if isinstance(data, list):
                error_msg = "Nenhum chat encontrado"
            self.status_bar.showMessage(f"❌ {error_msg}", 5000)

        self.progress_bar.setVisible(False)
        self.refresh_button.setText("🔄")

    def show_about(self):
        """Mostra informações sobre o aplicativo"""
        about_text = """
        <h2>🔥 WhatsApp Clone v2.0</h2>
        <p><b>Com Integração W-API</b></p>

        <h3>📋 Recursos:</h3>
        <ul>
            <li>✅ Interface moderna estilo WhatsApp Web</li>
            <li>🔌 Integração com W-API</li>
            <li>📱 QR Code para conectar WhatsApp</li>
            <li>📱 Envio e recebimento de mensagens reais</li>
            <li>👥 Sincronização de chats</li>
            <li>⚙️ Sistema de configuração</li>
            <li>🌙 Tema escuro</li>
        </ul>

        <h3>🛠️ Tecnologias:</h3>
        <ul>
            <li>Python 3.8+</li>
            <li>PyQt6</li>
            <li>Requests</li>
            <li>W-API.app</li>
        </ul>

        <p><i>Desenvolvido com ❤️ usando PyQt6</i></p>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Sobre")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(about_text)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #202C33;
                color: #E4E6EA;
            }
            QMessageBox QPushButton {
                background-color: #00D4AA;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        msg.exec()


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal da aplicação"""
    app = QApplication(sys.argv)
    app.setApplicationName("WhatsApp Clone - W-API")
    app.setOrganizationName("WhatsAppClone")
    app.setOrganizationDomain("whatsappclone.local")

    # Ícone da aplicação (se existir)
    # app.setWindowIcon(QIcon("icon.png"))

    window = WhatsAppClone()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()