#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Janela principal COMPLETA com envio de mensagens
Integração total: texto, imagens, áudio, stickers, documentos, localização
"""

import sys
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QLabel, QProgressBar,
    QVBoxLayout, QWidget, QSplitter, QFrame
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QObject, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QTcpSocket, QHostAddress

# Importar módulos necessários
from ui.main_window_ui import MainWindowUI, ContactItemWidget
from ui.chat_widget import MessageRenderer, MessageBubble
from database_fixed import ChatDatabaseInterface
from whatsapp_api_client import WhatsAppAPIClient, MessageSender, MessagePreparator
from enhanced_input_widget import EnhancedInputWidget, FilePreviewWidget


class WebSocketClient(QObject):
    """Cliente WebSocket para receber mensagens em tempo real"""

    new_message_received = pyqtSignal(dict)
    connection_status_changed = pyqtSignal(bool)

    def __init__(self, host="localhost", port=8765):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = QTcpSocket()
        self.setup_connections()

    def setup_connections(self):
        """Configura conexões do socket"""
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.on_data_received)
        self.socket.errorOccurred.connect(self.on_error)

    def connect_to_server(self):
        """Conecta ao servidor WebSocket"""
        print(f"🔌 Tentando conectar ao WebSocket: {self.host}:{self.port}")
        self.socket.connectToHost(QHostAddress(self.host), self.port)

    def disconnect_from_server(self):
        """Desconecta do servidor"""
        if self.socket.state() == QTcpSocket.SocketState.ConnectedState:
            self.socket.disconnectFromHost()

    @pyqtSlot()
    def on_connected(self):
        """Chamado quando conecta com sucesso"""
        print("✅ WebSocket conectado para mensagens em tempo real")
        self.connection_status_changed.emit(True)

    @pyqtSlot()
    def on_disconnected(self):
        """Chamado quando desconecta"""
        print("❌ WebSocket desconectado")
        self.connection_status_changed.emit(False)

    @pyqtSlot()
    def on_data_received(self):
        """Processa dados recebidos"""
        try:
            data = self.socket.readAll().data().decode('utf-8')
            if data:
                for line in data.strip().split('\n'):
                    if line:
                        message_data = json.loads(line)
                        print(f"📨 Nova mensagem recebida via WebSocket: {message_data.get('messageId', 'N/A')}")
                        self.new_message_received.emit(message_data)
        except Exception as e:
            print(f"⚠️ Erro ao processar dados WebSocket: {e}")

    def on_error(self, error):
        """Trata erros de conexão"""
        print(f"⚠️ Erro WebSocket: {error}")


class DatabaseWorker(QThread):
    """Worker thread OTIMIZADO para operações específicas do banco"""

    contacts_loaded = pyqtSignal(list)
    messages_loaded = pyqtSignal(list, bool)
    old_messages_loaded = pyqtSignal(list)
    single_message_processed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool)
    progress_update = pyqtSignal(str, int)
    task_completed = pyqtSignal(str)

    def __init__(self, db_interface: ChatDatabaseInterface):
        super().__init__()
        self.db_interface = db_interface
        self.current_task = None
        self.task_params = {}
        self._should_stop = False

    def set_task(self, task_name: str, **params):
        """Define tarefa otimizada"""
        self.current_task = task_name
        self.task_params = params
        self._should_stop = False

    def stop_task(self):
        """Para a tarefa atual"""
        self._should_stop = True

    def run(self):
        """Executa tarefas otimizadas"""
        try:
            if not self.db_interface.is_connected():
                self.connection_status_changed.emit(False)
                self.error_occurred.emit("Banco de dados não conectado")
                return

            self.connection_status_changed.emit(True)

            if self._should_stop:
                return

            if self.current_task == "load_contacts":
                self.progress_update.emit("Carregando contatos...", 0)
                contacts = self.db_interface.get_chats_list(50)
                if not self._should_stop:
                    self.contacts_loaded.emit(contacts)
                    self.task_completed.emit("load_contacts")

            elif self.current_task == "load_messages_initial":
                chat_id = self.task_params.get('chat_id')
                if chat_id:
                    self.progress_update.emit("Carregando mensagens iniciais...", 0)
                    messages = self.db_interface.get_chat_messages(chat_id, 50)
                    if not self._should_stop:
                        self.messages_loaded.emit(messages, True)
                        self.task_completed.emit("load_messages_initial")

            elif self.current_task == "load_old_messages":
                chat_id = self.task_params.get('chat_id')
                before_timestamp = self.task_params.get('before_timestamp')
                limit = self.task_params.get('limit', 20)

                if chat_id and before_timestamp:
                    self.progress_update.emit("Carregando mensagens antigas...", 0)
                    old_messages = self.db_interface.get_messages_before(chat_id, before_timestamp, limit)
                    if not self._should_stop:
                        self.old_messages_loaded.emit(old_messages)
                        self.task_completed.emit("load_old_messages")

            elif self.current_task == "process_new_message":
                message_data = self.task_params.get('message_data')
                if message_data:
                    processed_msg = self.db_interface.process_single_message(message_data)
                    if processed_msg and not self._should_stop:
                        self.single_message_processed.emit(processed_msg)
                        self.task_completed.emit("process_new_message")

        except Exception as e:
            if not self._should_stop:
                self.error_occurred.emit(f"Erro na operação: {str(e)}")

    def stop(self):
        """Para worker thread"""
        self._should_stop = True
        self.quit()
        self.wait(3000)


class CompleteWhatsAppWindow(QMainWindow):
    """Janela principal COMPLETA com envio de mensagens"""

    def __init__(self):
        super().__init__()

        # Estado otimizado
        self._is_loading = False
        self._current_contact = None
        self._current_contact_data = None
        self._loaded_contacts = {}
        self._message_widgets = {}
        self._oldest_message_timestamp = None
        self._is_at_bottom = True
        self._loading_old_messages = False

        # Inicializar componentes
        print("🚀 Inicializando sistema completo de mensagens...")
        self.setup_database()
        self.setup_api_client()
        self.setup_ui()
        self.setup_websocket()
        self.setup_workers()
        self.setup_connections()

        # Inicialização
        QTimer.singleShot(300, self.load_initial_data)
        QTimer.singleShot(1000, self.websocket_client.connect_to_server)

    def setup_database(self):
        """Inicializa interface do banco"""
        self.db_interface = ChatDatabaseInterface()

    def setup_api_client(self):
        """Inicializa cliente da API WhatsApp"""
        self.api_client = WhatsAppAPIClient(
            base_url="http://localhost:3000",
            session_name="default"
        )

        # Thread para envio de mensagens
        self.message_sender = MessageSender(self.api_client)
        self.setup_message_sender_connections()

    def setup_ui(self):
        """Configura interface completa"""
        # UI base
        self.ui = MainWindowUI(self)

        # Substituir área de entrada por versão aprimorada
        self.setup_enhanced_input()

    def setup_enhanced_input(self):
        """Substitui área de entrada por versão aprimorada"""
        # Remover entrada antiga da UI base
        old_input = self.ui.message_input.parent()
        old_input.setVisible(False)

        # Criar nova entrada aprimorada
        self.enhanced_input = EnhancedInputWidget()

        # Adicionar à interface
        chat_widget = self.ui.chat_stack.widget(1)  # Widget do chat ativo
        chat_layout = chat_widget.layout()
        chat_layout.removeWidget(old_input)  # Remove entrada antiga
        chat_layout.addWidget(self.enhanced_input)  # Adiciona nova

        # Conectar sinais da entrada aprimorada
        self.setup_enhanced_input_connections()

    def setup_enhanced_input_connections(self):
        """Conecta sinais da entrada aprimorada"""
        self.enhanced_input.send_text_message.connect(self.send_text_message)
        self.enhanced_input.send_file_message.connect(self.send_file_message)
        self.enhanced_input.send_audio_message.connect(self.send_audio_message)
        self.enhanced_input.send_location_message.connect(self.send_location_message)

    def setup_websocket(self):
        """Configura WebSocket"""
        self.websocket_client = WebSocketClient()
        self.websocket_client.new_message_received.connect(self.on_new_message_websocket)
        self.websocket_client.connection_status_changed.connect(self.on_websocket_status)

    def setup_workers(self):
        """Configura workers"""
        self.db_worker = DatabaseWorker(self.db_interface)
        self.setup_database_connections()

        # Timers
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.try_websocket_reconnect)
        self.reconnect_timer.start(30000)

        self.backup_check_timer = QTimer()
        self.backup_check_timer.timeout.connect(self.backup_message_check)
        self.backup_check_timer.start(60000)

    def setup_database_connections(self):
        """Configura conexões do banco"""
        self.db_worker.contacts_loaded.connect(self.on_contacts_loaded)
        self.db_worker.messages_loaded.connect(self.on_messages_loaded)
        self.db_worker.old_messages_loaded.connect(self.on_old_messages_loaded)
        self.db_worker.single_message_processed.connect(self.on_single_message_added)
        self.db_worker.error_occurred.connect(self.on_database_error)
        self.db_worker.connection_status_changed.connect(self.on_connection_status_changed)
        self.db_worker.progress_update.connect(self.on_progress_update)
        self.db_worker.task_completed.connect(self.on_task_completed)

    def setup_message_sender_connections(self):
        """Configura conexões do enviador de mensagens"""
        self.message_sender.message_sent.connect(self.on_message_sent_success)
        self.message_sender.send_error.connect(self.on_message_send_error)
        self.message_sender.upload_progress.connect(self.on_upload_progress)

    def setup_connections(self):
        """Conecta sinais da UI"""
        self.ui.refresh_btn.clicked.connect(self.refresh_current_chat)
        self.ui.search_input.textChanged.connect(self.filter_contacts)

        # Scroll para paginação reversa
        scrollbar = self.ui.messages_scroll.verticalScrollBar()
        scrollbar.valueChanged.connect(self.on_scroll_changed)

        # Atalhos
        from PyQt6.QtGui import QShortcut, QKeySequence
        debug_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        debug_shortcut.activated.connect(self.show_debug_info)

    # === MÉTODOS DE ENVIO DE MENSAGENS ===

    @pyqtSlot(str)
    def send_text_message(self, text: str):
        """Envia mensagem de texto"""
        if not self._current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro!")
            return

        if not text.strip():
            return

        print(f"📤 Enviando texto: {text[:50]}...")

        # Formatar número
        formatted_number = MessagePreparator.format_phone_number(self._current_contact)

        # Preparar mensagem
        message_data = MessagePreparator.prepare_text_message(formatted_number, text)

        # Mostrar progresso
        self.enhanced_input.show_progress("Enviando mensagem...", 0)

        # Adicionar à fila de envio
        self.message_sender.add_message_to_queue(message_data)

        # Criar mensagem temporária na interface
        self.create_temporary_message(text, 'text')

    @pyqtSlot(str, str)
    def send_file_message(self, file_path: str, file_type: str):
        """Envia arquivo (imagem, documento, áudio)"""
        if not self._current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro!")
            return

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Erro", "Arquivo não encontrado!")
            return

        # Validar arquivo
        validation = MessagePreparator.validate_file_for_whatsapp(file_path, file_type)
        if not validation["valid"]:
            QMessageBox.warning(self, "Arquivo Inválido", validation["error"])
            return

        print(f"📤 Enviando {file_type}: {os.path.basename(file_path)}")

        # Para imagens, mostrar preview
        if file_type == "image":
            self.show_file_preview(file_path, file_type)
        else:
            self.send_file_directly(file_path, file_type)

    def show_file_preview(self, file_path: str, file_type: str):
        """Mostra preview do arquivo antes de enviar"""
        preview_widget = FilePreviewWidget(file_path, file_type)
        preview_widget.send_confirmed.connect(self.on_file_preview_confirmed)
        preview_widget.send_cancelled.connect(lambda: preview_widget.close())

        # Centralizar na tela
        preview_widget.move(
            self.x() + (self.width() - preview_widget.width()) // 2,
            self.y() + (self.height() - preview_widget.height()) // 2
        )

        preview_widget.show()

    @pyqtSlot(str, str, str)
    def on_file_preview_confirmed(self, file_path: str, file_type: str, caption: str):
        """Confirmação do envio do arquivo"""
        self.send_file_directly(file_path, file_type, caption)

    def send_file_directly(self, file_path: str, file_type: str, caption: str = ""):
        """Envia arquivo diretamente"""
        formatted_number = MessagePreparator.format_phone_number(self._current_contact)

        # Preparar mensagem baseada no tipo
        if file_type == "image":
            message_data = MessagePreparator.prepare_image_message(formatted_number, file_path, caption)
        elif file_type == "audio":
            message_data = MessagePreparator.prepare_audio_message(formatted_number, file_path)
        elif file_type == "document":
            filename = os.path.basename(file_path)
            message_data = MessagePreparator.prepare_document_message(formatted_number, file_path, filename)
        else:
            QMessageBox.warning(self, "Erro", f"Tipo de arquivo não suportado: {file_type}")
            return

        # Mostrar progresso
        file_name = os.path.basename(file_path)
        self.enhanced_input.show_progress(f"Enviando {file_name}...", 0)

        # Adicionar à fila
        self.message_sender.add_message_to_queue(message_data)

        # Criar mensagem temporária
        content = f"📎 {file_name}"
        if caption:
            content += f"\n{caption}"
        self.create_temporary_message(content, file_type)

    @pyqtSlot(str)
    def send_audio_message(self, audio_path: str):
        """Envia mensagem de áudio"""
        if not self._current_contact:
            return

        self.send_file_directly(audio_path, "audio")

    @pyqtSlot(float, float, str)
    def send_location_message(self, latitude: float, longitude: float, name: str):
        """Envia localização"""
        if not self._current_contact:
            QMessageBox.warning(self, "Aviso", "Selecione um contato primeiro!")
            return

        print(f"📍 Enviando localização: {name} ({latitude}, {longitude})")

        formatted_number = MessagePreparator.format_phone_number(self._current_contact)
        message_data = MessagePreparator.prepare_location_message(formatted_number, latitude, longitude, name)

        # Mostrar progresso
        self.enhanced_input.show_progress("Enviando localização...", 0)

        # Adicionar à fila
        self.message_sender.add_message_to_queue(message_data)

        # Criar mensagem temporária
        self.create_temporary_message(f"📍 {name}", 'location')

    def create_temporary_message(self, content: str, message_type: str):
        """Cria mensagem temporária na interface"""
        try:
            temp_message = {
                'message_id': f"temp_{datetime.now().timestamp()}",
                'sender_name': "Você",
                'content': content,
                'timestamp': datetime.now().timestamp(),
                'timestamp_str': datetime.now().strftime('%H:%M'),
                'date_str': datetime.now().strftime('%d/%m/%Y'),
                'from_me': True,
                'is_group': self._current_contact_data.get('is_group', False) if self._current_contact_data else False,
                'message_type': message_type,
                'media_data': None,
                'sender_id': '',
                'is_temporary': True  # Marcar como temporária
            }

            self.on_single_message_added(temp_message)

        except Exception as e:
            print(f"⚠️ Erro ao criar mensagem temporária: {e}")

    # === CALLBACKS DE ENVIO ===

    @pyqtSlot(dict, dict)
    def on_message_sent_success(self, message_data: Dict, api_response: Dict):
        """Chamado quando mensagem é enviada com sucesso"""
        print(f"✅ Mensagem enviada com sucesso: {message_data.get('type', 'unknown')}")

        # Esconder progresso
        self.enhanced_input.hide_progress()

        # TODO: Marcar mensagem temporária como enviada
        # ou aguardar confirmação via WebSocket

    @pyqtSlot(str)
    def on_message_send_error(self, error_message: str):
        """Chamado quando há erro no envio"""
        print(f"❌ Erro no envio: {error_message}")

        # Esconder progresso
        self.enhanced_input.hide_progress()

        # Mostrar erro ao usuário
        QMessageBox.warning(
            self,
            "Erro no Envio",
            f"Não foi possível enviar a mensagem:\n\n{error_message}"
        )

    @pyqtSlot(int)
    def on_upload_progress(self, progress: int):
        """Atualiza progresso do upload"""
        self.enhanced_input.update_progress(progress)

    # === MÉTODOS HERDADOS E ADAPTADOS ===

    def on_scroll_changed(self, value):
        """Detecta mudanças no scroll para paginação reversa"""
        scrollbar = self.ui.messages_scroll.verticalScrollBar()

        if value == scrollbar.minimum() and not self._loading_old_messages and self._current_contact:
            self.load_older_messages()

        self._is_at_bottom = (value >= scrollbar.maximum() - 50)

    def load_older_messages(self):
        """Carrega mensagens mais antigas"""
        if not self._current_contact or not self._oldest_message_timestamp:
            return

        print(f"📜 Carregando mensagens antigas antes de {self._oldest_message_timestamp}")
        self._loading_old_messages = True

        if self.db_worker.isRunning():
            self.db_worker.stop_task()
            self.db_worker.wait(1000)

        self.db_worker.set_task(
            "load_old_messages",
            chat_id=self._current_contact,
            before_timestamp=self._oldest_message_timestamp,
            limit=20
        )
        self.db_worker.start()

    @pyqtSlot(dict)
    def on_new_message_websocket(self, message_data: Dict):
        """Processa nova mensagem recebida via WebSocket"""
        try:
            if not self._current_contact:
                return

            # Determinar se pertence ao chat atual
            is_group = message_data.get('isGroup', False)
            from_me = message_data.get('fromMe', False)

            if is_group:
                chat_id = message_data.get('chat', {}).get('id', '')
            else:
                if from_me:
                    chat_id = message_data.get('chat', {}).get('id', '')
                else:
                    chat_id = message_data.get('sender', {}).get('id', '')

            if chat_id == self._current_contact:
                print(f"📨 Nova mensagem para o chat atual: {chat_id}")

                if self.db_worker.isRunning():
                    self.db_worker.wait(500)

                self.db_worker.set_task("process_new_message", message_data=message_data)
                self.db_worker.start()
            else:
                print(f"📨 Nova mensagem para outro chat: {chat_id}")
                self.update_contact_in_list(message_data)

        except Exception as e:
            print(f"⚠️ Erro ao processar mensagem WebSocket: {e}")

    def on_single_message_added(self, processed_message: Dict):
        """Adiciona uma única mensagem nova"""
        try:
            if not self._current_contact:
                return

            print("📨 Adicionando nova mensagem...")

            # Verificar se precisa de separador de data
            message_timestamp = processed_message.get('timestamp', 0)
            message_dt = datetime.fromtimestamp(message_timestamp)
            message_date = message_dt.strftime('%d/%m/%Y')

            layout_count = self.ui.messages_layout.count()
            needs_date_separator = True

            if layout_count > 1:
                for i in range(layout_count - 1, -1, -1):
                    item = self.ui.messages_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if isinstance(widget, MessageBubble):
                            last_date = widget.message_data.get('date_str', '')
                            current_date = processed_message.get('date_str', '')
                            needs_date_separator = (last_date != current_date)
                            break

            # Remover stretch temporariamente
            stretch_item = None
            if layout_count > 0:
                last_item = self.ui.messages_layout.itemAt(layout_count - 1)
                if last_item and last_item.spacerItem():
                    stretch_item = self.ui.messages_layout.takeAt(layout_count - 1)

            # Adicionar separador de data se necessário
            if needs_date_separator:
                try:
                    formatted_date = MessageRenderer.format_date_separator(message_date)
                    date_separator = MessageRenderer.create_date_separator(formatted_date)
                    if date_separator:
                        self.ui.messages_layout.addWidget(date_separator)
                except Exception as e:
                    print(f"⚠️ Erro separador nova mensagem: {e}")

            # Criar e adicionar a nova mensagem
            message_widget = MessageRenderer.create_message_widget(processed_message)
            if message_widget:
                self.ui.messages_layout.addWidget(message_widget)

                msg_id = processed_message.get('message_id', f"new_{datetime.now().timestamp()}")
                self._message_widgets[msg_id] = message_widget

                # Animar entrada
                if isinstance(message_widget, MessageBubble):
                    QTimer.singleShot(50, message_widget.animate_in)

            # Restaurar stretch
            if stretch_item:
                self.ui.messages_layout.addItem(stretch_item)
            else:
                self.ui.messages_layout.addStretch()

            # Scroll automático apenas se estava no final
            if self._is_at_bottom:
                QTimer.singleShot(100, self.ui.scroll_to_bottom)

            print("✅ Nova mensagem adicionada")

        except Exception as e:
            print(f"⚠️ Erro ao adicionar mensagem única: {e}")

    # === MÉTODOS BASE ADAPTADOS ===

    def load_initial_data(self):
        """Carrega dados iniciais"""
        print("📥 Carregando lista de contatos...")
        self.ui.show_welcome_screen()

        if self.db_interface.is_connected():
            self.start_loading("Carregando conversas...")

            if self.db_worker.isRunning():
                self.db_worker.stop_task()
                self.db_worker.wait(1000)

            self.db_worker.set_task("load_contacts")
            self.db_worker.start()
        else:
            self.show_connection_error()

    def on_contacts_loaded(self, contacts: List[Dict]):
        """Carrega contatos"""
        print(f"📋 {len(contacts)} contatos carregados")
        self.update_contacts_list(contacts)

    def update_contacts_list(self, contacts: List[Dict]):
        """Atualiza lista de contatos"""
        self.ui.clear_contacts_list()
        self._loaded_contacts.clear()

        if not contacts:
            self.show_no_contacts_message()
            return

        for idx, contact_data in enumerate(contacts):
            try:
                contact_widget = self.ui.add_contact_to_list(contact_data)
                contact_widget.clicked.connect(self.on_contact_selected)

                contact_id = contact_data['chat_id']
                self._loaded_contacts[contact_id] = contact_data

            except Exception as e:
                print(f"⚠️ Erro ao adicionar contato {idx}: {e}")
                continue

        print(f"✅ Lista atualizada: {len(self._loaded_contacts)} conversas")

    def on_contact_selected(self, contact_id: str):
        """Seleciona contato e carrega mensagens"""
        if contact_id not in self._loaded_contacts or self._is_loading:
            return

        contact_data = self._loaded_contacts[contact_id]
        print(f"👤 Selecionado: {contact_data['chat_name'][:30]}")

        # Atualizar estado
        self._current_contact = contact_id
        self._current_contact_data = contact_data
        self._oldest_message_timestamp = None
        self._is_at_bottom = True

        # Limpar cache
        self._message_widgets.clear()

        # Atualizar UI
        self.ui.show_chat_screen()
        self.ui.update_active_contact(contact_data)
        self.ui.clear_messages()

        # Habilitar entrada aprimorada
        self.enhanced_input.set_current_contact(contact_id)

        # Carregar mensagens
        self.start_loading("Carregando mensagens...")

        if self.db_worker.isRunning():
            self.db_worker.stop_task()
            self.db_worker.wait(1000)

        self.db_worker.set_task("load_messages_initial", chat_id=contact_id)
        self.db_worker.start()

    def on_messages_loaded(self, messages: List[Dict], is_initial: bool):
        """Carrega mensagens iniciais"""
        if not self._current_contact:
            return

        print(f"💬 {len(messages)} mensagens carregadas")

        if is_initial:
            self.render_initial_messages(messages)

    def render_initial_messages(self, messages: List[Dict]):
        """Renderiza mensagens iniciais"""
        self.ui.clear_messages()
        QApplication.processEvents()

        if not messages:
            self.add_system_message("Nenhuma mensagem encontrada nesta conversa.")
            return

        # Ordenar cronologicamente
        try:
            messages_sorted = sorted(messages, key=lambda x: x.get('timestamp', 0))
        except:
            messages_sorted = messages

        # Definir timestamp da mensagem mais antiga
        if messages_sorted:
            self._oldest_message_timestamp = messages_sorted[0].get('timestamp', 0)

        print("🎨 Renderizando mensagens iniciais...")

        previous_message = None
        widgets_added = 0
        current_date = None

        for i, message_data in enumerate(messages_sorted):
            try:
                if i % 10 == 0:
                    QApplication.processEvents()

                # Verificar separador de data
                try:
                    message_dt = datetime.fromtimestamp(message_data.get('timestamp', 0))
                    message_date = message_dt.strftime('%d/%m/%Y')
                except:
                    message_date = message_data.get('date_str', '')

                if message_date and message_date != current_date:
                    try:
                        formatted_date = MessageRenderer.format_date_separator(message_date)
                        date_separator = MessageRenderer.create_date_separator(formatted_date)
                        if date_separator:
                            self.ui.messages_layout.addWidget(date_separator)
                            widgets_added += 1
                        current_date = message_date
                    except Exception as e:
                        print(f"⚠️ Erro separador: {e}")

                # Criar mensagem
                try:
                    message_widget = MessageRenderer.create_message_widget(message_data)
                    if message_widget:
                        self.ui.messages_layout.addWidget(message_widget)

                        msg_id = message_data.get('message_id', f"msg_{i}")
                        self._message_widgets[msg_id] = message_widget
                        widgets_added += 1

                        if isinstance(message_widget, MessageBubble):
                            QTimer.singleShot(50 + (i * 20), message_widget.animate_in)

                except Exception as e:
                    print(f"⚠️ Erro mensagem {i}: {e}")
                    continue

                previous_message = message_data

            except Exception as e:
                print(f"⚠️ Erro na mensagem {i}: {e}")
                continue

        # Finalizar
        try:
            QTimer.singleShot(100, lambda: self.ui.messages_layout.addStretch())
            QTimer.singleShot(200, self.update_messages_geometry)
            QTimer.singleShot(300, self.ui.scroll_to_bottom)

            print(f"✅ {widgets_added} mensagens renderizadas")

        except Exception as e:
            print(f"⚠️ Erro na finalização: {e}")

    # === MÉTODOS AUXILIARES ===

    def start_loading(self, message: str = "Carregando..."):
        """Inicia loading"""
        self._is_loading = True
        print(f"🔄 {message}")

    def stop_loading(self):
        """Para loading"""
        self._is_loading = False

    def on_progress_update(self, message: str, percent: int):
        """Atualiza progresso"""
        if self._is_loading:
            print(f"📊 {message} ({percent}%)")

    def on_task_completed(self, task_name: str):
        """Tarefa concluída"""
        self.stop_loading()
        print(f"✅ Tarefa concluída: {task_name}")

    def on_connection_status_changed(self, connected: bool):
        """Atualiza status de conexão"""
        self.ui.update_connection_status(connected)

        if connected:
            print("✅ Conectado ao banco")
        else:
            print("❌ Desconectado do banco")
            if self._is_loading:
                self.stop_loading()

    def on_old_messages_loaded(self, old_messages: List[Dict]):
        """Adiciona mensagens antigas no topo"""
        if not old_messages or not self._current_contact:
            self._loading_old_messages = False
            return

        print(f"📜 Adicionando {len(old_messages)} mensagens antigas no topo")

        # Salvar posição do scroll
        scrollbar = self.ui.messages_scroll.verticalScrollBar()
        old_scroll_value = scrollbar.value()
        old_maximum = scrollbar.maximum()

        # Atualizar timestamp
        if old_messages:
            self._oldest_message_timestamp = min(msg.get('timestamp', 0) for msg in old_messages)

        # Renderizar mensagens antigas no TOPO
        current_date = None
        widgets_added = 0

        for i, message_data in enumerate(sorted(old_messages, key=lambda x: x.get('timestamp', 0))):
            try:
                # Verificar separador de data
                message_dt = datetime.fromtimestamp(message_data.get('timestamp', 0))
                message_date = message_dt.strftime('%d/%m/%Y')

                if message_date != current_date:
                    try:
                        formatted_date = MessageRenderer.format_date_separator(message_date)
                        date_separator = MessageRenderer.create_date_separator(formatted_date)
                        if date_separator:
                            self.ui.messages_layout.insertWidget(widgets_added, date_separator)
                            widgets_added += 1
                        current_date = message_date
                    except Exception as e:
                        print(f"⚠️ Erro separador: {e}")

                # Criar mensagem
                message_widget = MessageRenderer.create_message_widget(message_data)
                if message_widget:
                    self.ui.messages_layout.insertWidget(widgets_added, message_widget)

                    msg_id = message_data.get('message_id', f"temp_{i}")
                    self._message_widgets[msg_id] = message_widget
                    widgets_added += 1

            except Exception as e:
                print(f"⚠️ Erro mensagem antiga {i}: {e}")
                continue

        # Restaurar posição do scroll
        QTimer.singleShot(50, lambda: self.restore_scroll_position(old_scroll_value, old_maximum))

        self._loading_old_messages = False
        print(f"✅ {widgets_added} mensagens antigas adicionadas")

    def restore_scroll_position(self, old_value, old_maximum):
        """Restaura posição do scroll após adicionar mensagens antigas"""
        scrollbar = self.ui.messages_scroll.verticalScrollBar()
        new_maximum = scrollbar.maximum()
        new_value = old_value + (new_maximum - old_maximum)
        scrollbar.setValue(new_value)

    def update_contact_in_list(self, message_data: Dict):
        """Atualiza contato na lista sem recarregar tudo"""
        try:
            is_group = message_data.get('isGroup', False)
            from_me = message_data.get('fromMe', False)

            if is_group:
                chat_id = message_data.get('chat', {}).get('id', '')
                chat_name = message_data.get('chat', {}).get('name', 'Grupo')
            else:
                if from_me:
                    chat_id = message_data.get('chat', {}).get('id', '')
                    chat_name = self.db_interface.get_contact_name(chat_id)
                else:
                    chat_id = message_data.get('sender', {}).get('id', '')
                    chat_name = message_data.get('sender', {}).get('pushName',
                                                                   '') or self.db_interface.get_contact_name(chat_id)

            # Buscar widget na lista
            for i in range(self.ui.contacts_list.count()):
                item = self.ui.contacts_list.item(i)
                if item:
                    widget = self.ui.contacts_list.itemWidget(item)
                    if isinstance(widget, ContactItemWidget):
                        if widget.contact_data.get('chat_id') == chat_id:
                            # Atualizar dados
                            widget.contact_data['last_message'] = self.extract_message_content(message_data)
                            widget.contact_data['last_message_time'] = message_data.get('moment', 0)
                            widget.contact_data['last_message_from_me'] = from_me

                            # Mover para o topo
                            item_widget = self.ui.contacts_list.takeItem(i)
                            self.ui.contacts_list.insertItem(0, item_widget)
                            break

        except Exception as e:
            print(f"⚠️ Erro ao atualizar contato: {e}")

    def extract_message_content(self, msg: Dict) -> str:
        """Extrai conteúdo da mensagem para preview"""
        msg_content = msg.get('msgContent', {})

        if 'conversation' in msg_content:
            return msg_content['conversation']
        elif 'stickerMessage' in msg_content:
            return '🏷️ Sticker'
        elif 'imageMessage' in msg_content:
            return '📷 Imagem'
        elif 'videoMessage' in msg_content:
            return '🎥 Vídeo'
        elif 'audioMessage' in msg_content:
            return '🎵 Áudio'
        elif 'documentMessage' in msg_content:
            return '📄 Documento'
        elif 'locationMessage' in msg_content:
            return '📍 Localização'
        else:
            return '📱 Mensagem'

    def update_messages_geometry(self):
        """Atualiza geometria das mensagens"""
        try:
            if hasattr(self.ui, 'messages_widget'):
                self.ui.messages_widget.updateGeometry()
            if hasattr(self.ui, 'messages_scroll'):
                self.ui.messages_scroll.updateGeometry()
            QApplication.processEvents()
        except Exception as e:
            print(f"⚠️ Erro ao atualizar geometria: {e}")

    def add_system_message(self, message: str):
        """Adiciona mensagem do sistema"""
        try:
            system_label = QLabel(message)
            system_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            self.ui.messages_layout.addWidget(system_label)
            print(f"📝 Sistema: {message}")

        except Exception as e:
            print(f"⚠️ Erro mensagem sistema: {e}")

    def filter_contacts(self, search_text: str):
        """Filtra contatos"""
        if self._is_loading:
            return

        search_text = search_text.lower().strip()

        if not search_text:
            for i in range(self.ui.contacts_list.count()):
                item = self.ui.contacts_list.item(i)
                if item:
                    item.setHidden(False)
            return

        hidden_count = 0
        for i in range(self.ui.contacts_list.count()):
            item = self.ui.contacts_list.item(i)
            if not item:
                continue

            widget = self.ui.contacts_list.itemWidget(item)
            if isinstance(widget, ContactItemWidget):
                contact_data = widget.contact_data
                name = contact_data.get('chat_name', '').lower()
                contact_id = contact_data.get('chat_id', '').lower()
                last_message = contact_data.get('last_message', '').lower()

                should_show = (search_text in name or
                               search_text in contact_id or
                               search_text in last_message)

                item.setHidden(not should_show)
                if not should_show:
                    hidden_count += 1

        print(f"🔍 '{search_text}' - {hidden_count} ocultos")

    def refresh_current_chat(self):
        """Atualiza chat atual"""
        if self._is_loading:
            return

        if self._current_contact:
            print(f"🔄 Verificando atualizações: {self._current_contact[:15]}")
            self.backup_message_check()
        else:
            print("🔄 Atualizando lista de contatos")
            self.load_initial_data()

    def on_websocket_status(self, connected: bool):
        """Atualiza status WebSocket"""
        if connected:
            print("✅ WebSocket conectado - mensagens em tempo real ativadas")
        else:
            print("❌ WebSocket desconectado - usando verificação por timer")

    def try_websocket_reconnect(self):
        """Tenta reconectar WebSocket"""
        if self.websocket_client.socket.state() != self.websocket_client.socket.SocketState.ConnectedState:
            print("🔄 Tentando reconectar WebSocket...")
            self.websocket_client.connect_to_server()

    def backup_message_check(self):
        """Verificação backup caso WebSocket falhe"""
        if not self._current_contact:
            return

        if self.websocket_client.socket.state() != self.websocket_client.socket.SocketState.ConnectedState:
            try:
                latest_messages = self.db_interface.get_chat_messages(self._current_contact, 5)

                if latest_messages:
                    last_widget_timestamp = 0
                    layout_count = self.ui.messages_layout.count()

                    for i in range(layout_count - 1, -1, -1):
                        item = self.ui.messages_layout.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if isinstance(widget, MessageBubble):
                                last_widget_timestamp = widget.message_data.get('timestamp', 0)
                                break

                    for msg in latest_messages:
                        if msg.get('timestamp', 0) > last_widget_timestamp:
                            print("📨 Nova mensagem detectada via backup check")
                            self.on_single_message_added(msg)

            except Exception as e:
                print(f"⚠️ Erro na verificação backup: {e}")

    def on_database_error(self, error_message: str):
        """Trata erros do banco"""
        print(f"❌ Erro no banco: {error_message}")

        if self._is_loading:
            self.stop_loading()

        self.ui.update_connection_status(False)

    def show_debug_info(self):
        """Informações de debug"""
        print(f"🔍 DEBUG INFO:")
        print(f"   Contato atual: {self._current_contact}")
        print(f"   Loading ativo: {self._is_loading}")
        print(f"   Worker rodando: {self.db_worker.isRunning()}")
        print(f"   Contatos em cache: {len(self._loaded_contacts)}")
        print(f"   Widgets mensagens: {len(self._message_widgets)}")
        print(f"   WebSocket conectado: {self.websocket_client.socket.state()}")

        # Verificar status da API
        if self.api_client.check_connection():
            print(f"   API WhatsApp: ✅ Conectada")
        else:
            print(f"   API WhatsApp: ❌ Desconectada")

        if self._current_contact:
            layout_count = self.ui.messages_layout.count()
            print(f"   Widgets no layout: {layout_count}")

    def show_no_contacts_message(self):
        """Mostra mensagem quando não há contatos"""
        print("📭 Nenhuma conversa encontrada")

    def show_connection_error(self):
        """Mostra erro de conexão"""
        print("❌ Erro de conexão com banco")
        self.ui.update_connection_status(False)

    def closeEvent(self, event):
        """Fecha aplicação"""
        print("👋 Encerrando aplicação completa...")

        # Desconectar WebSocket
        if hasattr(self, 'websocket_client'):
            self.websocket_client.disconnect_from_server()

        # Parar timers
        if hasattr(self, 'reconnect_timer'):
            self.reconnect_timer.stop()
        if hasattr(self, 'backup_check_timer'):
            self.backup_check_timer.stop()

        # Parar workers
        if hasattr(self, 'db_worker') and self.db_worker.isRunning():
            self.db_worker.stop()

        if hasattr(self, 'message_sender') and self.message_sender.isRunning():
            self.message_sender.stop_sending()

        event.accept()


def main():
    """Função principal COMPLETA"""
    app = QApplication(sys.argv)

    app.setApplicationName("WhatsApp Chat Interface - COMPLETO")
    app.setApplicationVersion("4.0.0")
    app.setOrganizationName("Chat Analytics")

    try:
        app.setWindowIcon(QIcon("icon.png"))
    except:
        pass

    print("\n🚀 Iniciando interface COMPLETA com envio de mensagens...")

    # Verificar dependências
    required_modules = [
        'requests',
        'PyQt6'
    ]

    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print("❌ Módulos em falta:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\n📦 Instale com: pip install " + " ".join(missing_modules))
        return

    try:
        window = CompleteWhatsAppWindow()
        window.show()

        print("🎉 Interface COMPLETA iniciada!")
        print("\n💡 RECURSOS IMPLEMENTADOS:")
        print("   ✅ Envio de mensagens de texto")
        print("   ✅ Envio de imagens com legenda")
        print("   ✅ Envio de documentos")
        print("   ✅ Gravação e envio de áudio")
        print("   ✅ Envio de localização")
        print("   ✅ Painel de emojis interativo")
        print("   ✅ Preview de arquivos antes do envio")
        print("   ✅ Barra de progresso de upload")
        print("   ✅ Validação de arquivos WhatsApp")
        print("   ✅ Integração com API de envio")
        print("   ✅ WebSocket para tempo real")
        print("   ✅ Suporte a todos os tipos de mídia")

        print("\n⌨️ ATALHOS DISPONÍVEIS:")
        print("   • Enter: Enviar mensagem de texto")
        print("   • Ctrl+Enter: Nova linha no texto")
        print("   • 📎: Menu de anexos")
        print("   • 😊: Painel de emojis")
        print("   • 🎤: Gravar áudio (clique e segure)")
        print("   • ➤: Enviar texto (quando há texto)")

        print("\n🔧 CONFIGURAÇÃO NECESSÁRIA:")
        print("   1. API WhatsApp rodando em http://localhost:3000")
        print("   2. WebSocket em localhost:8765 (opcional)")
        print("   3. Banco SQLite configurado")

        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

# =============================================================================
# 🎨 INTERFACE COMPLETA - WHATSAPP CHAT COM ENVIO
# =============================================================================
#
# 📋 ARQUIVOS NECESSÁRIOS:
# - main_window_complete.py (este arquivo - controlador principal)
# - whatsapp_api_client.py (cliente da API WhatsApp)
# - enhanced_input_widget.py (widget de entrada aprimorado)
# - database_fixed.py (interface do banco otimizada)
# - ui/main_window_ui.py (layout da interface)
# - ui/chat_widget.py (balões de mensagem)
# - backend/banco/database_manager_updated.py (gerenciador do banco)
# - backend/banco/models_updated.py (modelos do banco)
# - backend/banco/whatsapp_webhook_realtime.db (banco SQLite)
#
# 🚀 COMO EXECUTAR:
# python main_window_complete.py
#
# 🎯 RECURSOS COMPLETOS:
# ✅ Interface fofa com cores pastéis
# ✅ Lista de contatos com busca
# ✅ Balões de mensagem estilo Messenger
# ✅ Integração completa com banco SQLite
# ✅ ENVIO DE MENSAGENS DE TEXTO
# ✅ ENVIO DE IMAGENS COM LEGENDA
# ✅ ENVIO DE DOCUMENTOS
# ✅ GRAVAÇÃO E ENVIO DE ÁUDIO
# ✅ ENVIO DE LOCALIZAÇÃO
# ✅ PAINEL DE EMOJIS INTERATIVO
# ✅ PREVIEW DE ARQUIVOS
# ✅ BARRA DE PROGRESSO
# ✅ VALIDAÇÃO DE ARQUIVOS
# ✅ INTEGRAÇÃO COM API WHATSAPP
# ✅ WEBSOCKET TEMPO REAL
# ✅ Suporte a todos os tipos de mensagem
# ✅ Separadores de data automáticos
# ✅ Atualização automática
# ✅ Design responsivo
# ✅ Animações suaves
# ✅ Paginação reversa (scroll infinito)
#
# 📱 TIPOS DE MENSAGEM SUPORTADOS:
# - 💬 Texto/emoji (com painel de emojis)
# - 🏷️ Stickers
# - 📷 Imagens (com preview e legenda)
# - 🎥 Vídeos (com preview)
# - 🎵 Áudios (gravação e arquivo)
# - 📄 Documentos (todos os tipos)
# - 📍 Localizações (com mapa)
# - 📊 Enquetes (visualização)
#
# 🔧 CONFIGURAÇÃO DA API:
# 1. Configure sua API WhatsApp em http://localhost:3000
# 2. Endpoints necessários:
#    - POST /client/sendMessage/{session}
#    - POST /client/sendFile/{session}
#    - POST /client/sendLocation/{session}
#    - GET /status
# 3. Configure WebSocket em localhost:8765 (opcional)
#
# =============================================================================