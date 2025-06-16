#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Janela principal INDEPENDENTE com integração WhatsApp API REAL
Versão completa sem dependências circulares
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Set
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMessageBox,
                             QFileDialog, QProgressBar, QLabel, QInputDialog)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon

# Importar nossos módulos principais
from ui.main_window_ui import MainWindowUI, ContactItemWidget
from ui.chat_widget import MessageRenderer, MessageBubble
from database import ChatDatabaseInterface

# Tentar importar WhatsApp API
try:
    from __whatsAppApi import WhatsAppAPI

    WHATSAPP_API_AVAILABLE = True
    print("✅ WhatsApp API disponível")
except ImportError:
    print("⚠️ WhatsApp API não encontrada")
    WHATSAPP_API_AVAILABLE = False


    # Mock da API para desenvolvimento
    class WhatsAppAPI:
        def __init__(self, instance_id, api_token, base_url=""):
            self.instance_id = instance_id
            self.api_token = api_token

        def checa_status_conexao(self, api_token, id_instance):
            return "disconnected"

        def envia_mensagem_texto(self, phone, message, delay=1):
            return {"status": "mock", "message": "API não disponível"}

def validate_message_ids(message_data: Dict) -> Dict:
    """Valida e corrige IDs de mensagem se necessário"""
    webhook_id = message_data.get('webhook_message_id') or message_data.get('message_id')
    chat_id = message_data.get('chat_id') or message_data.get('contact_id')

    corrections = {
        'webhook_id_ok': bool(webhook_id),
        'chat_id_ok': bool(chat_id),
        'corrections_made': []
    }

    # Corrigir webhook_id se necessário
    if not webhook_id:
        timestamp = message_data.get('timestamp', int(datetime.now().timestamp()))
        temp_id = f"temp_{timestamp}_{hash(str(message_data.get('content', '')))[:8]}"
        message_data['webhook_message_id'] = temp_id
        message_data['message_id'] = temp_id
        corrections['corrections_made'].append('webhook_id_generated')
        corrections['webhook_id_ok'] = True
        print(f"⚠️ Webhook ID gerado: {temp_id}")

    # Corrigir chat_id se necessário
    if not chat_id:
        # Tentar diferentes fontes para chat_id
        possible_chat_ids = [
            message_data.get('contact_id'),
            message_data.get('sender_id'),
            message_data.get('recipient_id')
        ]

        for possible_id in possible_chat_ids:
            if possible_id:
                message_data['chat_id'] = possible_id
                corrections['corrections_made'].append(f'chat_id_from_{possible_id}')
                corrections['chat_id_ok'] = True
                print(f"⚠️ Chat ID corrigido: {possible_id}")
                break

    if corrections['webhook_id_ok'] and corrections['chat_id_ok']:
        print(
            f"✅ IDs validados/corrigidos - Webhook: {message_data.get('webhook_message_id', '')[:15]}..., Chat: {message_data.get('chat_id', '')[:15]}...")
    else:
        print(f"❌ Falha na validação de IDs: {corrections}")

    return corrections


class WhatsAppConfig:
    """Configurações da API WhatsApp"""

    def __init__(self):
        self.INSTANCE_ID = "3B6XIW-ZTS923-GEAY6V"
        self.API_TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"
        self.BASE_URL = "https://api.w-api.app/v1/"
        self.load_from_file()

    def load_from_file(self):
        """Carrega configurações de arquivo JSON"""
        config_file = "whatsapp_config.json"

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)

                self.INSTANCE_ID = config.get('instance_id', self.INSTANCE_ID)
                self.API_TOKEN = config.get('api_token', self.API_TOKEN)
                self.BASE_URL = config.get('base_url', self.BASE_URL)

                print(f"✅ Configurações carregadas de {config_file}")

            except Exception as e:
                print(f"⚠️ Erro ao carregar configurações: {e}")
                self.save_to_file()
        else:
            self.save_to_file()

    def save_to_file(self):
        """Salva configurações em arquivo JSON"""
        config = {
            'instance_id': self.INSTANCE_ID,
            'api_token': self.API_TOKEN,
            'base_url': self.BASE_URL,
            'created_at': datetime.now().isoformat()
        }

        try:
            with open("whatsapp_config.json", 'w') as f:
                json.dump(config, f, indent=2)
            print("📄 Arquivo whatsapp_config.json criado")
        except Exception as e:
            print(f"⚠️ Erro ao salvar configurações: {e}")


class WhatsAppMessageSender(QThread):
    """Thread para envio de mensagens via WhatsApp API"""

    # Sinais
    message_sent = pyqtSignal(dict)
    message_failed = pyqtSignal(str, str)
    progress_update = pyqtSignal(int)
    connection_status = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        self.config = WhatsAppConfig()
        self.whatsapp_api = None
        self.message_queue = []
        self.is_sending = False
        self.stop_requested = False

        self.init_api()

    def init_api(self):
        """Inicializa a API do WhatsApp"""
        if not WHATSAPP_API_AVAILABLE:
            print("❌ WhatsAppAPI não disponível")
            return False

        try:
            self.whatsapp_api = WhatsAppAPI(
                instance_id=self.config.INSTANCE_ID,
                api_token=self.config.API_TOKEN,
                base_url=self.config.BASE_URL
            )

            status = self.whatsapp_api.checa_status_conexao(
                self.config.API_TOKEN,
                self.config.INSTANCE_ID
            )

            connected = status == "connected"
            self.connection_status.emit(connected)

            if connected:
                print("✅ WhatsApp API conectada")
            else:
                print("⚠️ WhatsApp API não conectada")

            return connected

        except Exception as e:
            print(f"❌ Erro ao inicializar WhatsApp API: {e}")
            self.connection_status.emit(False)
            return False

    def send_text_message_to_contact(self, contact_id: str, message: str):
        """Envia mensagem de texto"""
        if not message.strip():
            return

        message_data = {
            'type': 'text',
            'contact_id': self._format_phone_number(contact_id),
            'content': message.strip(),
            'timestamp': datetime.now().isoformat(),
            'temp_id': f"temp_{int(datetime.now().timestamp() * 1000)}"
        }

        self.message_queue.append(message_data)
        print(f"📝 Mensagem adicionada à fila: {contact_id}")

        if not self.is_sending:
            self.start()

    def send_file_to_contact(self, contact_id: str, file_path: str, file_type: str, caption: str = ""):
        """Envia arquivo"""
        if not os.path.exists(file_path):
            self.message_failed.emit(contact_id, f"Arquivo não encontrado: {file_path}")
            return

        message_data = {
            'type': 'file',
            'file_type': file_type,
            'contact_id': self._format_phone_number(contact_id),
            'file_path': file_path,
            'caption': caption,
            'timestamp': datetime.now().isoformat(),
            'temp_id': f"temp_{int(datetime.now().timestamp() * 1000)}"
        }

        self.message_queue.append(message_data)
        print(f"📎 Arquivo adicionado à fila: {file_type}")

        if not self.is_sending:
            self.start()

    def run(self):
        """Processa fila de mensagens"""
        self.is_sending = True

        while self.message_queue and not self.stop_requested:
            message_data = self.message_queue.pop(0)

            try:
                self.progress_update.emit(0)
                success = self._send_single_message(message_data)

                if success:
                    sent_message = self._create_sent_message_data(message_data)
                    self.message_sent.emit(sent_message)
                    self.progress_update.emit(100)
                else:
                    self.message_failed.emit(
                        message_data['contact_id'],
                        "Falha no envio"
                    )

            except Exception as e:
                error_msg = f"Erro no envio: {str(e)}"
                self.message_failed.emit(message_data['contact_id'], error_msg)

            if self.message_queue:
                self.msleep(500)

        self.is_sending = False
        self.progress_update.emit(0)

    def _send_single_message(self, message_data: Dict) -> bool:
        """Envia uma única mensagem e captura o ID real da resposta"""
        if not self.whatsapp_api:
            return False

        try:
            result = None

            if message_data['type'] == 'text':
                result = self.whatsapp_api.envia_mensagem_texto(
                    phone_number=message_data['contact_id'],
                    message=message_data['content'],
                    delay_message=1
                )

            elif message_data['type'] == 'file':
                file_type = message_data['file_type']
                file_path = message_data['file_path']
                caption = message_data.get('caption', '')
                contact_id = message_data['contact_id']

                self.progress_update.emit(25)

                if file_type == 'image':
                    result = self.whatsapp_api.enviar_imagem(
                        phone_number=contact_id,
                        image_path=file_path,
                        caption=caption
                    )
                elif file_type == 'document':
                    result = self.whatsapp_api.envia_documento(
                        phone_number=contact_id,
                        file_path=file_path,
                        caption=caption
                    )
                elif file_type == 'audio':
                    result = self.whatsapp_api.enviar_audio(
                        phone_number=contact_id,
                        audio_source=file_path
                    )
                elif file_type == 'video':
                    result = self.whatsapp_api.enviarGif(
                        phone_number=contact_id,
                        gif_source=file_path,
                        caption=caption
                    )
                else:
                    result = self.whatsapp_api.envia_documento(
                        phone_number=contact_id,
                        file_path=file_path,
                        caption=caption
                    )

                self.progress_update.emit(75)

            # ARMAZENAR a resposta da API para usar no _create_sent_message_data
            self._last_api_response = result if result else {}

            # Verificar resultado
            if result and isinstance(result, dict):
                print(f"✅ Mensagem enviada: {result}")

                # Log do messageId para debug
                if 'messageId' in result:
                    print(f"📋 ID real da mensagem: {result['messageId']}")

                return True
            else:
                print(f"❌ Falha no envio: {result}")
                return False

        except Exception as e:
            print(f"❌ Erro no envio: {e}")
            return False

    def _create_sent_message_data(self, message_data: Dict) -> Dict:
        """Cria dados da mensagem enviada com IDs corretos"""
        timestamp = int(datetime.now().timestamp())

        # OBTER O ID REAL DA RESPOSTA DA API se disponível
        api_response = getattr(self, '_last_api_response', {})
        real_message_id = api_response.get('messageId', message_data['temp_id'])

        if message_data['type'] == 'text':
            content = message_data['content']
            message_type = 'text'
            media_data = None
        else:
            file_path = message_data['file_path']
            filename = os.path.basename(file_path)
            caption = message_data.get('caption', '')

            if caption:
                content = f"{filename}: {caption}"
            else:
                content = filename

            message_type = message_data['file_type']
            media_data = {
                'filename': filename,
                'file_path': file_path,
                'caption': caption
            }

        # CORRIGIR: Incluir todos os IDs necessários
        return {
            'message_id': real_message_id,  # ID real da API ou temp_id se não disponível
            'webhook_message_id': real_message_id,  # ID para operações da API
            'local_message_id': message_data['temp_id'],  # ID temporário local
            'sender_name': 'Você',
            'content': content,
            'timestamp': timestamp,
            'timestamp_str': datetime.fromtimestamp(timestamp).strftime('%H:%M'),
            'date_str': datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y'),
            'from_me': True,
            'is_group': False,
            'message_type': message_type,
            'media_data': media_data,
            'sender_id': '',
            'contact_id': message_data['contact_id'],
            'chat_id': message_data['contact_id'],  # CORRIGIR: usar contact_id como chat_id
            'raw_webhook_data': {}  # Dados originais para debug
        }

    def _format_phone_number(self, phone: str) -> str:
        """Formata número de telefone"""
        phone_clean = ''.join(filter(str.isdigit, phone))

        if len(phone_clean) == 11 and not phone_clean.startswith('55'):
            phone_clean = '55' + phone_clean
        elif len(phone_clean) == 10 and not phone_clean.startswith('55'):
            phone_clean = '55' + phone_clean

        return phone_clean

    def check_connection(self) -> bool:
        """Verifica conexão"""
        if not self.whatsapp_api:
            return False

        try:
            status = self.whatsapp_api.checa_status_conexao(
                self.config.API_TOKEN,
                self.config.INSTANCE_ID
            )

            connected = status == "connected"
            self.connection_status.emit(connected)
            return connected

        except Exception as e:
            print(f"❌ Erro ao verificar conexão: {e}")
            self.connection_status.emit(False)
            return False

    def stop_sending(self):
        """Para envio"""
        self.stop_requested = True
        self.message_queue.clear()
        self.is_sending = False


class IncrementalUpdater(QThread):
    """Thread para atualizações incrementais"""

    new_messages_found = pyqtSignal(list)

    def __init__(self, db_interface: ChatDatabaseInterface):
        super().__init__()
        self.db_interface = db_interface
        self.is_running = True
        self.current_contact_id = None
        self.update_interval = 3000
        self.check_count = 0

    def set_current_contact(self, contact_id: str):
        """Define contato atual"""
        self.current_contact_id = contact_id
        self.check_count = 0
        print(f"🎯 Monitoramento ativo para: {contact_id[:15]}")

    def run(self):
        """Loop de verificação"""
        while self.is_running:
            try:
                if self.current_contact_id:
                    self.check_for_new_messages_incremental()
                self.msleep(self.update_interval)
            except Exception as e:
                print(f"Erro no updater: {e}")
                self.msleep(10000)

    def check_for_new_messages_incremental(self):
        """Verifica novas mensagens"""
        if not self.current_contact_id:
            return

        try:
            self.check_count += 1
            new_messages = self.db_interface.get_new_messages_incremental(self.current_contact_id)

            if new_messages:
                print(f"📬 {len(new_messages)} novas mensagens")
                self.new_messages_found.emit(new_messages)
            else:
                if self.check_count % 10 == 0:
                    print(f"🔍 Verificação #{self.check_count}: sem novas mensagens")

        except Exception as e:
            print(f"Erro na verificação: {e}")

    def stop(self):
        """Para updater"""
        self.is_running = False
        self.quit()
        self.wait()


class OptimizedDatabaseWorker(QThread):
    """Worker para operações do banco"""

    contacts_loaded = pyqtSignal(list)
    messages_loaded_initial = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool)

    def __init__(self, db_interface: ChatDatabaseInterface):
        super().__init__()
        self.db_interface = db_interface
        self.current_task = None
        self.task_params = {}
        self.is_running = True

    def set_task(self, task_name: str, **params):
        """Define tarefa"""
        self.current_task = task_name
        self.task_params = params

    def run(self):
        """Executa tarefa"""
        try:
            if not self.db_interface.is_connected():
                self.connection_status_changed.emit(False)
                self.error_occurred.emit("Banco não conectado")
                return

            self.connection_status_changed.emit(True)

            if self.current_task == "load_contacts":
                contacts = self.db_interface.get_contacts_list(50)
                self.contacts_loaded.emit(contacts)

            elif self.current_task == "load_messages_initial":
                contact_id = self.task_params.get('contact_id')
                limit = self.task_params.get('limit', 30)

                if contact_id:
                    print(f"⚡ Carregando mensagens para {contact_id[:15]}")
                    messages = self.db_interface.get_chat_messages_initial(contact_id, limit)
                    self.messages_loaded_initial.emit(messages)
                else:
                    self.error_occurred.emit("ID do contato não fornecido")

        except Exception as e:
            self.error_occurred.emit(f"Erro na operação: {str(e)}")

    def stop(self):
        """Para worker"""
        self.is_running = False
        self.quit()
        self.wait()


class WhatsAppChatMainWindow(QMainWindow):
    """Janela principal INDEPENDENTE com WhatsApp"""

    def __init__(self):
        super().__init__()

        # Inicializar banco
        self.db_interface = ChatDatabaseInterface()

        # Configurar UI
        self.ui = MainWindowUI(self)

        # Criar workers
        self.message_sender = WhatsAppMessageSender()
        self.db_worker = OptimizedDatabaseWorker(self.db_interface)
        self.incremental_updater = IncrementalUpdater(self.db_interface)

        # Conectar sinais
        self.setup_database_connections()
        self.setup_whatsapp_connections()
        self.setup_updater_connections()
        self.setup_ui_connections()

        # Estado
        self.current_contact = None
        self.current_contact_data = None
        self.loaded_contacts = {}
        self.is_loading_messages = False
        self.messages_loaded_count = 0

        # Timers
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_contacts)
        self.refresh_timer.start(60000)

        self.whatsapp_status_timer = QTimer()
        self.whatsapp_status_timer.timeout.connect(self.message_sender.check_connection)
        self.whatsapp_status_timer.start(30000)

        # Carregar dados
        self.load_initial_data()
        self.incremental_updater.start()

        # Verificação inicial WhatsApp
        QTimer.singleShot(2000, self.message_sender.check_connection)

    def setup_database_connections(self):
        """Conecta sinais do banco"""
        self.db_worker.contacts_loaded.connect(self.on_contacts_loaded)
        self.db_worker.messages_loaded_initial.connect(self.on_messages_loaded_initial)
        self.db_worker.error_occurred.connect(self.on_database_error)
        self.db_worker.connection_status_changed.connect(self.on_db_connection_status_changed)

    def setup_whatsapp_connections(self):
        """Conecta sinais do WhatsApp"""
        self.message_sender.message_sent.connect(self.on_whatsapp_message_sent)
        self.message_sender.message_failed.connect(self.on_whatsapp_message_failed)
        self.message_sender.progress_update.connect(self.on_whatsapp_progress)
        self.message_sender.connection_status.connect(self.on_whatsapp_connection_status)

    def setup_updater_connections(self):
        """Conecta sinais do updater"""
        self.incremental_updater.new_messages_found.connect(self.on_new_messages_received_incremental)

    def setup_ui_connections(self):
        """Conecta sinais da UI - VERSÃO ATUALIZADA"""
        self.ui.refresh_btn.clicked.connect(self.refresh_current_chat)
        self.ui.search_input.textChanged.connect(self.filter_contacts)
        self.ui.send_btn.clicked.connect(self.send_whatsapp_text_message)
        self.ui.attach_btn.clicked.connect(self.send_whatsapp_file)
        self.ui.message_input.returnPressed.connect(self.send_whatsapp_text_message)

        # Atalhos
        from PyQt6.QtGui import QShortcut, QKeySequence

        debug_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        debug_shortcut.activated.connect(self.show_debug_info)

        whatsapp_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        whatsapp_shortcut.activated.connect(self.show_whatsapp_config)

    def send_whatsapp_text_message(self):
        """Envia mensagem via WhatsApp"""
        if not self.current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro")
            return

        message_text = self.ui.message_input.text().strip()
        if not message_text:
            return

        # Limpar input
        self.ui.message_input.clear()

        # Desabilitar botão
        self.ui.send_btn.setEnabled(False)
        self.ui.send_btn.setText("📤...")

        # Enviar
        try:
            self.message_sender.send_text_message_to_contact(
                contact_id=self.current_contact,
                message=message_text
            )
            print(f"📱 Enviando: {message_text[:50]}...")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao enviar: {str(e)}")
            self.ui.send_btn.setEnabled(True)
            self.ui.send_btn.setText("📤")

    def send_whatsapp_file(self):
        """Envia arquivo via WhatsApp"""
        if not self.current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro")
            return

        # Selecionar arquivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo para WhatsApp",
            "",
            "Imagens (*.png *.jpg *.jpeg *.gif *.webp);;Documentos (*.pdf *.doc *.docx *.txt);;Áudios (*.mp3 *.wav *.ogg);;Vídeos (*.mp4 *.avi *.mov);;Todos (*.*)"
        )

        if not file_path:
            return

        # Determinar tipo
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            file_type = 'image'
        elif file_ext in ['.mp4', '.avi', '.mov', '.webm']:
            file_type = 'video'
        elif file_ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            file_type = 'audio'
        else:
            file_type = 'document'

        # Perguntar legenda
        caption = ""
        if file_type in ['image', 'video']:
            caption, ok = QInputDialog.getText(
                self,
                "Legenda",
                f"Legenda para {os.path.basename(file_path)} (opcional):"
            )
            if not ok:
                return

        # Desabilitar botão
        self.ui.attach_btn.setEnabled(False)
        self.ui.attach_btn.setText("📤...")

        # Enviar
        try:
            self.message_sender.send_file_to_contact(
                contact_id=self.current_contact,
                file_path=file_path,
                file_type=file_type,
                caption=caption if caption else ""
            )

            print(f"📎 Enviando {file_type}: {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao enviar arquivo: {str(e)}")
            self.ui.attach_btn.setEnabled(True)
            self.ui.attach_btn.setText("📎")

    def on_whatsapp_message_sent(self, message_data: Dict):
        """Mensagem WhatsApp enviada - com suporte a reações"""
        print(f"✅ Mensagem WhatsApp enviada: {message_data.get('content', '')[:50]}")

        # Reabilitar botões
        self.ui.send_btn.setEnabled(True)
        self.ui.send_btn.setText("📤")
        self.ui.attach_btn.setEnabled(True)
        self.ui.attach_btn.setText("📎")

        # VALIDAR E CORRIGIR IDs antes de adicionar à interface
        corrections = validate_message_ids(message_data)

        if not (corrections['webhook_id_ok'] and corrections['chat_id_ok']):
            print(f"❌ Não foi possível corrigir IDs da mensagem enviada")
            return

        # Adicionar à interface
        try:
            message_widget = MessageRenderer.create_message_widget(
                message_data,
                whatsapp_api=self.message_sender.whatsapp_api
            )
            if message_widget:
                self.add_single_message_to_chat(message_widget, message_data, is_sent=True)

                print(f"✅ Mensagem enviada adicionada à interface:")
                print(f"   Webhook ID: {message_data.get('webhook_message_id', '')}")
                print(f"   Chat ID: {message_data.get('chat_id', '')}")

        except Exception as e:
            print(f"Erro ao adicionar mensagem à UI: {e}")

    def on_whatsapp_message_failed(self, contact_id: str, error_message: str):
        """Falha no envio WhatsApp"""
        print(f"❌ Falha WhatsApp para {contact_id}: {error_message}")

        # Reabilitar botões
        self.ui.send_btn.setEnabled(True)
        self.ui.send_btn.setText("📤")
        self.ui.attach_btn.setEnabled(True)
        self.ui.attach_btn.setText("📎")

        # Mostrar erro
        QMessageBox.critical(self, "Erro WhatsApp", f"Falha no envio:\n{error_message}")

    def on_whatsapp_progress(self, progress: int):
        """Progresso do envio"""
        if progress < 100:
            self.ui.send_btn.setText(f"📤")
            self.ui.attach_btn.setText(f"📤")

    def on_whatsapp_connection_status(self, connected: bool):
        """Status da conexão WhatsApp"""
        if connected:
            print("✅ WhatsApp conectado")
        else:
            print("❌ WhatsApp desconectado")

    def on_message_deleted_from_ui(self, webhook_message_id: str, chat_id: str):
        """Callback quando mensagem é deletada na UI - Não remove da interface"""
        print(f"🗑️ Mensagem deletada via UI:")
        print(f"   Webhook ID: {webhook_message_id}")
        print(f"   Chat ID: {chat_id}")

        # Atualizar cache local
        try:
            if chat_id in self.db_interface._loaded_messages_cache:
                cache = self.db_interface._loaded_messages_cache[chat_id]
                if webhook_message_id in cache:
                    cache[webhook_message_id]['deleted'] = True
                    print("✅ Mensagem marcada como deletada no cache local")
        except Exception as e:
            print(f"⚠️ Erro ao atualizar cache: {e}")

    def on_message_edited_from_ui(self, webhook_message_id: str, new_text: str, chat_id: str):
        """Callback quando mensagem é editada na UI"""
        print(f"✏️ Mensagem editada via UI:")
        print(f"   Webhook ID: {webhook_message_id}")
        print(f"   Novo texto: {new_text[:50]}...")
        print(f"   Chat ID: {chat_id}")

        # Atualizar cache local
        try:
            if chat_id in self.db_interface._loaded_messages_cache:
                cache = self.db_interface._loaded_messages_cache[chat_id]
                if webhook_message_id in cache:
                    cache[webhook_message_id]['content'] = new_text
                    cache[webhook_message_id]['edited'] = True
                    print("✅ Cache local atualizado com edição")
        except Exception as e:
            print(f"⚠️ Erro ao atualizar cache: {e}")

    def on_message_reaction_from_ui(self, webhook_message_id: str, reaction: str, chat_id: str):
        """Callback quando reação é adicionada na UI"""
        print(f"😀 Reação aplicada via UI:")
        print(f"   Webhook ID: {webhook_message_id}")
        print(f"   Reação: {reaction}")
        print(f"   Chat ID: {chat_id}")

        # Atualizar cache local
        try:
            if chat_id in self.db_interface._loaded_messages_cache:
                cache = self.db_interface._loaded_messages_cache[chat_id]
                if webhook_message_id in cache:
                    cache[webhook_message_id]['reaction'] = reaction
                    print("✅ Cache local atualizado com reação")
        except Exception as e:
            print(f"⚠️ Erro ao atualizar cache: {e}")

    def show_whatsapp_config(self):
        """Mostra configurações WhatsApp"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTextEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("⚙️ Configurações WhatsApp")
        dialog.setFixedWidth(500)

        layout = QVBoxLayout(dialog)

        # Instance ID
        layout.addWidget(QLabel("Instance ID:"))
        instance_input = QLineEdit(self.message_sender.config.INSTANCE_ID)
        layout.addWidget(instance_input)

        # API Token
        layout.addWidget(QLabel("API Token:"))
        token_input = QLineEdit(self.message_sender.config.API_TOKEN)
        token_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(token_input)

        # Base URL
        layout.addWidget(QLabel("Base URL:"))
        url_input = QLineEdit(self.message_sender.config.BASE_URL)
        layout.addWidget(url_input)

        # Status
        layout.addWidget(QLabel("Status:"))
        status_text = QTextEdit()
        status_text.setMaximumHeight(80)
        status_text.setReadOnly(True)

        try:
            connected = self.message_sender.check_connection()
            if connected:
                status_text.setText("✅ Conectado!")
            else:
                status_text.setText("❌ Não conectado")
        except:
            status_text.setText("⚠️ Erro na verificação")

        layout.addWidget(status_text)

        # Botões
        button_layout = QHBoxLayout()

        test_btn = QPushButton("🧪 Testar")
        test_btn.clicked.connect(lambda: self.test_connection(status_text))

        save_btn = QPushButton("💾 Salvar")
        save_btn.clicked.connect(lambda: self.save_config(
            instance_input.text(),
            token_input.text(),
            url_input.text(),
            dialog
        ))

        cancel_btn = QPushButton("❌ Cancelar")
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(test_btn)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def test_connection(self, status_widget):
        """Testa conexão"""
        status_widget.setText("🔄 Testando...")
        QApplication.processEvents()

        try:
            connected = self.message_sender.check_connection()
            if connected:
                status_widget.setText("✅ Teste OK!")
            else:
                status_widget.setText("❌ Teste falhou")
        except Exception as e:
            status_widget.setText(f"⚠️ Erro: {str(e)}")

    def save_config(self, instance_id: str, api_token: str, base_url: str, dialog):
        """Salva configurações"""
        if not all([instance_id.strip(), api_token.strip(), base_url.strip()]):
            QMessageBox.warning(dialog, "Erro", "Todos os campos são obrigatórios")
            return

        try:
            self.message_sender.config.INSTANCE_ID = instance_id.strip()
            self.message_sender.config.API_TOKEN = api_token.strip()
            self.message_sender.config.BASE_URL = base_url.strip()

            # Salvar em arquivo
            self.message_sender.config.save_to_file()

            # Reinicializar API
            self.message_sender.init_api()

            QMessageBox.information(dialog, "Sucesso", "Configurações salvas!")
            dialog.accept()

        except Exception as e:
            QMessageBox.critical(dialog, "Erro", f"Erro ao salvar: {str(e)}")

    # ========== MÉTODOS DO BANCO E INTERFACE ==========

    def load_initial_data(self):
        """Carrega dados iniciais"""
        print("📥 Carregando contatos...")
        self.ui.show_welcome_screen()

        if self.db_interface.is_connected():
            self.db_worker.set_task("load_contacts")
            self.db_worker.start()
        else:
            QMessageBox.warning(self, "Erro", "Não foi possível conectar ao banco")

    def on_db_connection_status_changed(self, connected: bool):
        """Status do banco"""
        self.ui.update_connection_status(connected)

    def on_contacts_loaded(self, contacts: List[Dict]):
        """Contatos carregados"""
        print(f"📋 {len(contacts)} contatos carregados")

        self.ui.clear_contacts_list()
        self.loaded_contacts.clear()

        for contact_data in contacts:
            contact_widget = self.ui.add_contact_to_list(contact_data)
            contact_widget.clicked.connect(self.on_contact_selected)

            contact_id = contact_data['contact_id']
            self.loaded_contacts[contact_id] = contact_data

        print("✅ Lista atualizada")

    def on_contact_selected(self, contact_id: str):
        """Contato selecionado"""
        if contact_id not in self.loaded_contacts:
            return

        contact_data = self.loaded_contacts[contact_id]
        print(f"👤 Selecionado: {contact_data['contact_name']}")

        self.current_contact = contact_id
        self.current_contact_data = contact_data

        # Configurar updater
        self.incremental_updater.set_current_contact(contact_id)

        # Atualizar UI
        self.ui.show_chat_screen()
        self.ui.update_active_contact(contact_data)
        self.clear_messages_display()

        # Habilitar controles
        self.ui.message_input.setEnabled(True)
        self.ui.send_btn.setEnabled(True)
        self.ui.attach_btn.setEnabled(True)

        # Carregar mensagens
        self.is_loading_messages = True
        self.messages_loaded_count = 0

        self.db_worker.set_task("load_messages_initial", contact_id=contact_id, limit=30)

        if self.db_worker.isRunning():
            self.db_worker.wait()

        self.db_worker.start()

    def on_messages_loaded_initial(self, messages: List[Dict]):
        """Mensagens iniciais carregadas"""
        if not self.current_contact:
            return

        print(f"💬 {len(messages)} mensagens carregadas")
        self.is_loading_messages = False

        self.clear_messages_display()

        if not messages:
            self.add_system_message("Nenhuma mensagem encontrada")
            return

        # Renderizar mensagens
        previous_message = None
        self.messages_loaded_count = 0

        for i, message_data in enumerate(messages):
            # Separador de data
            if MessageRenderer.should_show_date_separator(message_data, previous_message):
                date_str = message_data.get('date_str', '')
                if date_str:
                    formatted_date = MessageRenderer.format_date_separator(date_str)
                    date_separator = MessageRenderer.create_date_separator(formatted_date)
                    self.add_widget_to_chat_initial(date_separator)

            # Criar mensagem
            try:
                message_widget = MessageRenderer.create_message_widget(
                    message_data,
                    whatsapp_api=self.message_sender.whatsapp_api
                )
                if message_widget:
                    if isinstance(message_widget, MessageBubble):
                        message_widget.message_date = message_data.get('date_str', '')

                    self.add_widget_to_chat_initial(message_widget)
                    self.messages_loaded_count += 1

                    # Animar
                    if isinstance(message_widget, MessageBubble):
                        QTimer.singleShot(20 * i, message_widget.animate_in)

            except Exception as e:
                print(f"Erro ao criar mensagem: {e}")
                continue

            previous_message = message_data

        # Stretch final
        self.ui.messages_layout.addStretch()

        # Atualizar geometria
        self.ui.messages_widget.updateGeometry()
        self.ui.messages_scroll.updateGeometry()

        QTimer.singleShot(200, self.ui.scroll_to_bottom)

        print(f"✅ {self.messages_loaded_count} mensagens renderizadas")

    def on_new_messages_received_incremental(self, new_messages: List[Dict]):
        """Novas mensagens incrementais - com suporte a reações"""
        if not new_messages:
            return

        print(f"📨 {len(new_messages)} novas mensagens")

        for message_data in new_messages:
            try:
                # Verificar se é uma reação a uma mensagem existente
                if self._is_reaction_update(message_data):
                    self._handle_reaction_update(message_data)
                    continue

                # Verificar se é uma edição de mensagem existente
                if self._is_message_edit(message_data):
                    self._handle_message_edit(message_data)
                    continue

                # Verificar se é uma exclusão de mensagem existente
                if self._is_message_deletion(message_data):
                    self._handle_message_deletion(message_data)
                    continue

                # Mensagem nova normal
                message_widget = MessageRenderer.create_message_widget(
                    message_data,
                    whatsapp_api=self.message_sender.whatsapp_api
                )
                if message_widget:
                    self.add_single_message_to_chat(message_widget, message_data, is_new=True)

            except Exception as e:
                print(f"Erro ao processar mensagem: {e}")

    def _is_reaction_update(self, message_data: Dict) -> bool:
        """Verifica se a mensagem é uma atualização de reação"""
        # Adapte esta lógica conforme seu banco de dados
        return (
                message_data.get('message_type') == 'reaction' or
                'reaction' in message_data and message_data.get('target_message_id')
        )

    def _is_reaction_update(self, message_data: Dict) -> bool:
        """Verifica se a mensagem é uma atualização de reação"""
        # Adapte esta lógica conforme seu banco de dados
        return (
                message_data.get('message_type') == 'reaction' or
                'reaction' in message_data and message_data.get('target_message_id')
        )

    def _handle_reaction_update(self, message_data: Dict):
        """Processa atualização de reação em mensagem existente"""
        target_message_id = message_data.get('target_message_id') or message_data.get('webhook_message_id')
        reaction = message_data.get('reaction', '')

        print(f"😀 Processando reação: {reaction} para mensagem {target_message_id}")

        # Encontrar widget da mensagem na interface
        message_widget = self._find_message_widget_by_id(target_message_id)
        if message_widget and isinstance(message_widget, MessageBubble):
            # Atualizar reação no widget
            message_widget.message_data['reaction'] = reaction
            message_widget._update_reaction_display(reaction)
            print(f"✅ Reação atualizada na interface")

    def _is_message_edit(self, message_data: Dict) -> bool:
        """Verifica se é uma edição de mensagem"""
        return (
                message_data.get('event_type') == 'message_edited' or
                message_data.get('edited', False)
        )

    def _handle_message_edit(self, message_data: Dict):
        """Processa edição de mensagem existente"""
        webhook_message_id = message_data.get('webhook_message_id') or message_data.get('message_id')
        new_content = message_data.get('content', '')

        print(f"✏️ Processando edição de mensagem {webhook_message_id}")

        # Encontrar widget da mensagem
        message_widget = self._find_message_widget_by_id(webhook_message_id)
        if message_widget and isinstance(message_widget, MessageBubble):
            # Atualizar conteúdo no widget
            message_widget.message_data['content'] = new_content
            message_widget.message_data['edited'] = True
            message_widget._show_as_edited(new_content)
            print(f"✅ Edição atualizada na interface")

    def _is_message_deletion(self, message_data: Dict) -> bool:
        """Verifica se é uma exclusão de mensagem"""
        return (
                message_data.get('event_type') == 'message_deleted' or
                message_data.get('deleted', False)
        )

    def _handle_message_deletion(self, message_data: Dict):
        """Processa exclusão de mensagem existente"""
        webhook_message_id = message_data.get('webhook_message_id') or message_data.get('message_id')

        print(f"🗑️ Processando exclusão de mensagem {webhook_message_id}")

        # Encontrar widget da mensagem
        message_widget = self._find_message_widget_by_id(webhook_message_id)
        if message_widget and isinstance(message_widget, MessageBubble):
            # Marcar como deletada no widget
            message_widget.message_data['deleted'] = True
            message_widget._show_as_deleted()
            print(f"✅ Exclusão atualizada na interface")

    def _find_message_widget_by_id(self, webhook_message_id: str) -> Optional[MessageBubble]:
        """Encontra widget de mensagem pelo ID do webhook"""
        try:
            # Percorrer widgets no layout de mensagens
            for i in range(self.ui.messages_layout.count()):
                item = self.ui.messages_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, MessageBubble):
                        widget_id = widget.message_data.get('webhook_message_id') or widget.message_data.get(
                            'message_id')
                        if widget_id == webhook_message_id:
                            return widget
            return None
        except Exception as e:
            print(f"Erro ao buscar widget: {e}")
            return None





    def add_single_message_to_chat(self, widget, message_data: Dict, is_sent: bool = False, is_new: bool = False):
        """Adiciona uma mensagem e conecta sinais corretamente"""
        try:
            # Conectar sinais da mensagem se for MessageBubble
            if isinstance(widget, MessageBubble):
                # Conectar sinais com IDs corretos
                widget.message_deleted.connect(self.on_message_deleted_from_ui)
                widget.message_edited.connect(self.on_message_edited_from_ui)
                widget.message_reaction.connect(self.on_message_reaction_from_ui)

            # Verificar separador de data (código existente...)
            need_date_separator = False
            last_widget_date = None

            if self.ui.messages_layout.count() > 1:
                for i in range(self.ui.messages_layout.count() - 1, -1, -1):
                    item = self.ui.messages_layout.itemAt(i)
                    if item and item.widget():
                        last_widget = item.widget()
                        if isinstance(last_widget, MessageBubble):
                            last_widget_date = getattr(last_widget, 'message_date', None)
                            break

            current_date = message_data.get('date_str', '')
            if current_date and last_widget_date and current_date != last_widget_date:
                need_date_separator = True
            elif current_date and not last_widget_date:
                need_date_separator = True

            # Remover stretch (código existente...)
            stretch_item = None
            if self.ui.messages_layout.count() > 0:
                last_item = self.ui.messages_layout.itemAt(self.ui.messages_layout.count() - 1)
                if last_item and last_item.spacerItem():
                    stretch_item = self.ui.messages_layout.takeAt(self.ui.messages_layout.count() - 1)

            # Adicionar separador se necessário (código existente...)
            if need_date_separator:
                formatted_date = MessageRenderer.format_date_separator(current_date)
                date_separator = MessageRenderer.create_date_separator(formatted_date)
                if date_separator:
                    date_separator.setVisible(True)
                    date_separator.show()
                    self.ui.messages_layout.addWidget(date_separator)

            # Adicionar mensagem
            widget.setVisible(True)
            widget.show()

            if isinstance(widget, MessageBubble):
                widget.message_date = current_date

            self.ui.messages_layout.addWidget(widget)

            # Readicionar stretch (código existente...)
            if stretch_item:
                self.ui.messages_layout.addItem(stretch_item)
            else:
                self.ui.messages_layout.addStretch()

            self.messages_loaded_count += 1
            self.ui.messages_widget.updateGeometry()

            # Animar (código existente...)
            if isinstance(widget, MessageBubble):
                if is_new or is_sent:
                    QTimer.singleShot(50, widget.animate_in)

            # Scroll (código existente...)
            if is_new or is_sent:
                QTimer.singleShot(100, self.ui.scroll_to_bottom)

            print(f"✅ Mensagem adicionada com sinais conectados. Total: {self.messages_loaded_count}")

        except Exception as e:
            print(f"❌ Erro ao adicionar mensagem: {e}")

    def add_widget_to_chat_initial(self, widget):
        """Adiciona widget inicial"""
        widget.setVisible(True)
        widget.show()
        self.ui.messages_layout.addWidget(widget)
        self.ui.messages_widget.updateGeometry()

    def clear_messages_display(self):
        """Limpa mensagens"""
        while self.ui.messages_layout.count() > 0:
            child = self.ui.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.messages_loaded_count = 0
        QApplication.processEvents()

    def on_database_error(self, error_message: str):
        """Erro no banco"""
        print(f"❌ Erro no banco: {error_message}")

    def add_system_message(self, message: str):
        """Adiciona mensagem do sistema"""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        system_label = QLabel(message)
        system_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        system_label.setFont(QFont('Segoe UI', 10))
        system_label.setMinimumHeight(40)
        system_label.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                background-color: #f8f9fa;
                padding: 10px 20px;
                border-radius: 15px;
                margin: 10px 50px;
                font-style: italic;
            }
        """)

        system_label.setVisible(True)
        system_label.show()
        self.add_widget_to_chat_initial(system_label)

    def filter_contacts(self, search_text: str):
        """Filtra contatos"""
        search_text = search_text.lower().strip()

        if not search_text:
            for i in range(self.ui.contacts_list.count()):
                item = self.ui.contacts_list.item(i)
                item.setHidden(False)
            return

        for i in range(self.ui.contacts_list.count()):
            item = self.ui.contacts_list.item(i)
            widget = self.ui.contacts_list.itemWidget(item)

            if isinstance(widget, ContactItemWidget):
                contact_data = widget.contact_data
                name = contact_data.get('contact_name', '').lower()
                contact_id = contact_data.get('contact_id', '').lower()

                should_show = (search_text in name or
                               search_text in contact_id or
                               search_text in contact_data.get('last_message', '').lower())

                item.setHidden(not should_show)

    def refresh_current_chat(self):
        """Refresh do chat"""
        if self.current_contact and not self.is_loading_messages:
            print(f"🔄 Refresh: {self.current_contact}")

            if self.incremental_updater.isRunning():
                self.incremental_updater.check_for_new_messages_incremental()

            try:
                new_messages = self.db_interface.get_new_messages_incremental(self.current_contact)
                if new_messages:
                    self.on_new_messages_received_incremental(new_messages)
                else:
                    print("✅ Sem novas mensagens")
            except Exception as e:
                print(f"❌ Erro no refresh: {e}")

    def auto_refresh_contacts(self):
        """Auto refresh contatos"""
        if not self.db_worker.isRunning() and not self.is_loading_messages:
            print("🔄 Auto-refresh contatos")
            self.db_worker.set_task("load_contacts")
            self.db_worker.start()

    def show_debug_info(self):
        """Debug info"""
        if self.current_contact:
            layout_count = self.ui.messages_layout.count()
            cache_stats = self.db_interface.get_cache_stats()

            print(f"🔍 DEBUG:")
            print(f"   Contato: {self.current_contact}")
            print(f"   Widgets: {layout_count}")
            print(f"   Mensagens: {self.messages_loaded_count}")
            print(f"   Cache: {cache_stats}")
            print(f"   WhatsApp API: {'Disponível' if self.message_sender.whatsapp_api else 'Indisponível'}")

    def closeEvent(self, event):
        """Fechamento"""
        print("👋 Encerrando...")

        # Parar timers
        self.refresh_timer.stop()
        self.whatsapp_status_timer.stop()

        # Parar threads
        if self.db_worker.isRunning():
            self.db_worker.stop()

        self.message_sender.stop_sending()

        if self.incremental_updater.isRunning():
            self.incremental_updater.stop()

        event.accept()


def main():
    """Função principal"""
    app = QApplication(sys.argv)

    app.setApplicationName("WhatsApp Chat - API Real Integrada")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("Chat Analytics")

    try:
        app.setWindowIcon(QIcon("icon.png"))
    except:
        pass

    try:
        window = WhatsAppChatMainWindow()
        window.show()

        print("🎉 Interface WhatsApp iniciada!")
        print("💡 RECURSOS:")

        if WHATSAPP_API_AVAILABLE:
            print("   ✅ WhatsApp API REAL disponível")
            print("   ✅ Envio real de mensagens")
            print("   ✅ Envio real de arquivos")
            print("   ✅ Verificação de conexão")
        else:
            print("   ⚠️ WhatsApp API não disponível")

        print("   ✅ Interface sem recarregamento")
        print("   ✅ Cache inteligente")
        print("   ✅ Atualizações incrementais")

        print("\n⌨️ CONTROLES:")
        print("   📱 Digite mensagens e pressione Enter")
        print("   📎 Clique para anexar arquivos")
        print("   ⚙️ Ctrl+W: Configurações WhatsApp")
        print("   🔍 Ctrl+D: Debug")

        print(f"\n📊 STATUS:")
        print(f"   WhatsApp API: {'🟢 Disponível' if WHATSAPP_API_AVAILABLE else '🔴 Indisponível'}")

        if WHATSAPP_API_AVAILABLE:
            print("\n🔧 PRIMEIRA CONFIGURAÇÃO:")
            print("   1. Pressione Ctrl+W para configurar")
            print("   2. Digite Instance ID e API Token")
            print("   3. Teste a conexão")
            print("   4. Comece a enviar mensagens!")

        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

# =============================================================================
# 🎨 INTERFACE WHATSAPP INDEPENDENTE - SEM DEPENDÊNCIAS CIRCULARES
# =============================================================================
#
# 📋 PRINCIPAIS CORREÇÕES:
# ✅ Arquivo independente sem imports circulares
# ✅ Classes OptimizedDatabaseWorker e IncrementalUpdater incluídas
# ✅ WhatsAppMessageSender integrado
# ✅ WhatsAppConfig para configurações
# ✅ Interface completa de configuração (Ctrl+W)
# ✅ Tratamento de erros robusto
# ✅ Mock da API quando não disponível
#
# 🔧 ESTRUTURA:
# - WhatsAppConfig: Gerencia configurações (whatsapp_config.json)
# - WhatsAppMessageSender: Thread para envio via API real
# - IncrementalUpdater: Thread para atualizações incrementais
# - OptimizedDatabaseWorker: Thread para operações do banco
# - WhatsAppChatMainWindow: Janela principal integrada
#
# 🎯 FUNCIONALIDADES:
# ✅ Envio real de mensagens de texto
# ✅ Envio real de arquivos (imagem, documento, áudio, vídeo)
# ✅ Verificação de status de conexão
# ✅ Configuração visual completa
# ✅ Cache inteligente sem recarregamento
# ✅ Atualizações incrementais suaves
# ✅ Tratamento específico de erros
# ✅ Feedback visual de progresso
#
# 🚀 USO:
# 1. Execute: python main_window_independent.py
# 2. Configure WhatsApp: Ctrl+W
# 3. Selecione um contato
# 4. Digite mensagens ou anexe arquivos
# 5. Mensagens são enviadas via API real!
#
# =============================================================================