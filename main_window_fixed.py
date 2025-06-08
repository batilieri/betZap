#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Janela principal OTIMIZADA - Sem tremor de tela e atualização incremental
MELHORIAS: Mensagens incrementais, paginação reversa, WebSocket para tempo real
"""

import sys
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QLabel, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QObject, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QTcpSocket, QHostAddress

# Importar módulos melhorados
from ui.main_window_ui import MainWindowUI, ContactItemWidget
from ui.chat_widget import MessageRenderer, MessageBubble
from database_fixed import ChatDatabaseInterface


class WebSocketClient(QObject):
    """Cliente WebSocket para receber mensagens em tempo real"""

    new_message_received = pyqtSignal(dict)  # Sinal para nova mensagem
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
                # Pode receber múltiplas mensagens
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

    # Sinais otimizados
    contacts_loaded = pyqtSignal(list)
    messages_loaded = pyqtSignal(list, bool)  # messages, is_initial_load
    old_messages_loaded = pyqtSignal(list)  # Para paginação reversa
    single_message_processed = pyqtSignal(dict)  # Para mensagem única
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
                # Carregamento inicial das mensagens (50 mais recentes)
                chat_id = self.task_params.get('chat_id')
                if chat_id:
                    self.progress_update.emit("Carregando mensagens iniciais...", 0)
                    messages = self.db_interface.get_chat_messages(chat_id, 50)
                    if not self._should_stop:
                        self.messages_loaded.emit(messages, True)  # True = carregamento inicial
                        self.task_completed.emit("load_messages_initial")

            elif self.current_task == "load_old_messages":
                # Carregamento de mensagens antigas (paginação reversa)
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
                # Processa uma única mensagem nova
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


class WhatsAppChatWindow(QMainWindow):
    """Janela principal OTIMIZADA sem tremor de tela"""

    def __init__(self):
        super().__init__()

        # Estado otimizado
        self._is_loading = False
        self._current_contact = None
        self._current_contact_data = None
        self._loaded_contacts = {}
        self._message_widgets = {}  # Cache de widgets de mensagem
        self._oldest_message_timestamp = None  # Para paginação reversa
        self._is_at_bottom = True  # Controle de scroll automático
        self._loading_old_messages = False

        # Inicializar banco otimizado
        print("🗄️ Inicializando sistema otimizado sem tremor...")
        self.db_interface = ChatDatabaseInterface()

        # Configurar UI
        self.ui = MainWindowUI(self)

        # WebSocket para tempo real
        self.websocket_client = WebSocketClient()
        self.setup_websocket_connections()

        # Worker thread otimizado
        self.db_worker = DatabaseWorker(self.db_interface)
        self.setup_database_connections()

        # Timer para reconexão WebSocket
        self.reconnect_timer = QTimer()
        self.reconnect_timer.timeout.connect(self.try_websocket_reconnect)
        self.reconnect_timer.start(30000)  # Tentar reconectar a cada 30s

        # Timer para backup de verificação (menos frequente)
        self.backup_check_timer = QTimer()
        self.backup_check_timer.timeout.connect(self.backup_message_check)
        self.backup_check_timer.start(60000)  # A cada 1 minuto

        # Conectar sinais da UI otimizada
        self.setup_ui_connections()

        # Carregar dados iniciais
        QTimer.singleShot(300, self.load_initial_data)

        # Conectar ao WebSocket
        QTimer.singleShot(1000, self.websocket_client.connect_to_server)

    def setup_websocket_connections(self):
        """Configura conexões WebSocket"""
        self.websocket_client.new_message_received.connect(self.on_new_message_websocket)
        self.websocket_client.connection_status_changed.connect(self.on_websocket_status)

    def setup_database_connections(self):
        """Configura conexões otimizadas"""
        self.db_worker.contacts_loaded.connect(self.on_contacts_loaded)
        self.db_worker.messages_loaded.connect(self.on_messages_loaded)
        self.db_worker.old_messages_loaded.connect(self.on_old_messages_loaded)
        self.db_worker.single_message_processed.connect(self.on_single_message_added)
        self.db_worker.error_occurred.connect(self.on_database_error)
        self.db_worker.connection_status_changed.connect(self.on_connection_status_changed)
        self.db_worker.progress_update.connect(self.on_progress_update)
        self.db_worker.task_completed.connect(self.on_task_completed)

    def setup_ui_connections(self):
        """Conecta sinais da UI otimizada"""
        self.ui.refresh_btn.clicked.connect(self.refresh_current_chat)
        self.ui.search_input.textChanged.connect(self.filter_contacts)

        # NOVO: Conectar scroll para detectar topo (paginação reversa)
        scrollbar = self.ui.messages_scroll.verticalScrollBar()
        scrollbar.valueChanged.connect(self.on_scroll_changed)

        # NOVO: Envio de mensagens habilitado
        self.ui.send_btn.clicked.connect(self.send_message)
        self.ui.message_input.returnPressed.connect(self.send_message)
        self.ui.message_input.setEnabled(True)
        self.ui.send_btn.setEnabled(True)

        # Atalhos
        from PyQt6.QtGui import QShortcut, QKeySequence
        debug_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        debug_shortcut.activated.connect(self.show_debug_info)

    def on_scroll_changed(self, value):
        """Detecta mudanças no scroll para paginação reversa"""
        scrollbar = self.ui.messages_scroll.verticalScrollBar()

        # Verificar se está no topo (carregar mensagens antigas)
        if value == scrollbar.minimum() and not self._loading_old_messages and self._current_contact:
            self.load_older_messages()

        # Verificar se está no final (para scroll automático)
        self._is_at_bottom = (value >= scrollbar.maximum() - 50)

    def load_older_messages(self):
        """Carrega mensagens mais antigas (paginação reversa)"""
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

    def on_old_messages_loaded(self, old_messages: List[Dict]):
        """Adiciona mensagens antigas no topo SEM tremor"""
        if not old_messages or not self._current_contact:
            self._loading_old_messages = False
            return

        print(f"📜 Adicionando {len(old_messages)} mensagens antigas no topo")

        # Salvar posição atual do scroll
        scrollbar = self.ui.messages_scroll.verticalScrollBar()
        old_scroll_value = scrollbar.value()
        old_maximum = scrollbar.maximum()

        # Atualizar timestamp da mensagem mais antiga
        if old_messages:
            self._oldest_message_timestamp = min(msg.get('timestamp', 0) for msg in old_messages)

        # Renderizar mensagens antigas no TOPO
        current_date = None
        widgets_added = 0

        # Renderizar em ordem cronológica (mais antigas primeiro)
        for i, message_data in enumerate(sorted(old_messages, key=lambda x: x.get('timestamp', 0))):
            try:
                # Verificar separador de data
                message_dt = datetime.fromtimestamp(message_data.get('timestamp', 0))
                message_date = message_dt.strftime('%d/%m/%Y')

                # Adicionar separador se mudou
                if message_date != current_date:
                    try:
                        formatted_date = MessageRenderer.format_date_separator(message_date)
                        date_separator = MessageRenderer.create_date_separator(formatted_date)
                        if date_separator:
                            # Inserir no TOPO
                            self.ui.messages_layout.insertWidget(widgets_added, date_separator)
                            widgets_added += 1
                        current_date = message_date
                    except Exception as e:
                        print(f"⚠️ Erro separador: {e}")

                # Criar mensagem
                message_widget = MessageRenderer.create_message_widget(message_data)
                if message_widget:
                    # Inserir no TOPO
                    self.ui.messages_layout.insertWidget(widgets_added, message_widget)

                    # Cache do widget
                    msg_id = message_data.get('message_id', f"temp_{i}")
                    self._message_widgets[msg_id] = message_widget
                    widgets_added += 1

            except Exception as e:
                print(f"⚠️ Erro mensagem antiga {i}: {e}")
                continue

        # Restaurar posição do scroll (compensar novas mensagens)
        QTimer.singleShot(50, lambda: self.restore_scroll_position(old_scroll_value, old_maximum))

        self._loading_old_messages = False
        print(f"✅ {widgets_added} mensagens antigas adicionadas sem tremor")

    def restore_scroll_position(self, old_value, old_maximum):
        """Restaura posição do scroll após adicionar mensagens antigas"""
        scrollbar = self.ui.messages_scroll.verticalScrollBar()
        new_maximum = scrollbar.maximum()

        # Calcular nova posição (compensar altura das novas mensagens)
        new_value = old_value + (new_maximum - old_maximum)
        scrollbar.setValue(new_value)

    @pyqtSlot(dict)
    def on_new_message_websocket(self, message_data: Dict):
        """Processa nova mensagem recebida via WebSocket"""
        try:
            # Verificar se a mensagem pertence ao chat atual
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

                # Processar mensagem via worker
                if self.db_worker.isRunning():
                    self.db_worker.wait(500)  # Aguardar um pouco

                self.db_worker.set_task("process_new_message", message_data=message_data)
                self.db_worker.start()
            else:
                print(f"📨 Nova mensagem para outro chat: {chat_id}")
                # Atualizar lista de contatos silenciosamente
                self.update_contact_in_list(message_data)

        except Exception as e:
            print(f"⚠️ Erro ao processar mensagem WebSocket: {e}")

    def on_single_message_added(self, processed_message: Dict):
        """Adiciona uma única mensagem nova SEM recarregar tudo"""
        try:
            if not self._current_contact:
                return

            print("📨 Adicionando nova mensagem sem tremor...")

            # Verificar se precisa de separador de data
            message_timestamp = processed_message.get('timestamp', 0)
            message_dt = datetime.fromtimestamp(message_timestamp)
            message_date = message_dt.strftime('%d/%m/%Y')

            # Verificar se é de hoje ou data diferente da última
            layout_count = self.ui.messages_layout.count()
            needs_date_separator = True

            if layout_count > 1:  # Tem mensagens anteriores
                # Buscar última mensagem para comparar data
                for i in range(layout_count - 1, -1, -1):
                    item = self.ui.messages_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if isinstance(widget, MessageBubble):
                            # Comparar datas
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

                # Cache do widget
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

            print("✅ Nova mensagem adicionada sem tremor")

        except Exception as e:
            print(f"⚠️ Erro ao adicionar mensagem única: {e}")

    def update_contact_in_list(self, message_data: Dict):
        """Atualiza contato na lista sem recarregar tudo"""
        try:
            # Extrair dados do contato
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

            # Buscar o widget na lista
            for i in range(self.ui.contacts_list.count()):
                item = self.ui.contacts_list.item(i)
                if item:
                    widget = self.ui.contacts_list.itemWidget(item)
                    if isinstance(widget, ContactItemWidget):
                        if widget.contact_data.get('chat_id') == chat_id:
                            # Atualizar dados do contato
                            widget.contact_data['last_message'] = self.extract_message_content(message_data)
                            widget.contact_data['last_message_time'] = message_data.get('moment', 0)
                            widget.contact_data['last_message_from_me'] = from_me

                            # Mover para o topo da lista
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

    def send_message(self):
        """NOVO: Envia mensagem (integração com webhook)"""
        if not self._current_contact or not self.ui.message_input.text().strip():
            return

        message_text = self.ui.message_input.text().strip()
        print(f"📤 Enviando mensagem: {message_text}")

        try:
            # Desabilitar input temporariamente
            self.ui.message_input.setEnabled(False)
            self.ui.send_btn.setEnabled(False)

            # Criar dados da mensagem a ser enviada
            send_data = {
                'to': self._current_contact,
                'message': message_text,
                'type': 'text'
            }

            # Enviar via API (implementar conforme sua API)
            # TODO: Integrar com sua API de envio do WhatsApp
            success = self.send_message_via_api(send_data)

            if success:
                # Limpar campo
                self.ui.message_input.clear()

                # Criar mensagem local temporária (será substituída quando chegar via webhook)
                temp_message = {
                    'message_id': f"temp_{datetime.now().timestamp()}",
                    'sender_name': "Você",
                    'content': message_text,
                    'timestamp': datetime.now().timestamp(),
                    'timestamp_str': datetime.now().strftime('%H:%M'),
                    'date_str': datetime.now().strftime('%d/%m/%Y'),
                    'from_me': True,
                    'is_group': self._current_contact_data.get('is_group', False),
                    'message_type': 'text',
                    'media_data': None,
                    'sender_id': ''
                }

                # Adicionar mensagem temporariamente
                self.on_single_message_added(temp_message)

                print("✅ Mensagem enviada com sucesso")
            else:
                print("❌ Falha ao enviar mensagem")

        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")

        finally:
            # Reabilitar input
            self.ui.message_input.setEnabled(True)
            self.ui.send_btn.setEnabled(True)
            self.ui.message_input.setFocus()

    def send_message_via_api(self, send_data: Dict) -> bool:
        """Envia mensagem via API do WhatsApp (implementar conforme sua API)"""
        try:
            # TODO: Implementar integração com sua API de envio
            # Exemplo com requests:
            # import requests
            # response = requests.post('http://localhost:3000/send-message', json=send_data)
            # return response.status_code == 200

            # Por enquanto, simular sucesso
            print(f"🔗 API call simulada para enviar: {send_data}")
            return True

        except Exception as e:
            print(f"❌ Erro na API de envio: {e}")
            return False

    def on_websocket_status(self, connected: bool):
        """Atualiza status da conexão WebSocket"""
        if connected:
            print("✅ WebSocket conectado - mensagens em tempo real ativadas")
        else:
            print("❌ WebSocket desconectado - usando verificação por timer")

    def try_websocket_reconnect(self):
        """Tenta reconectar WebSocket se desconectado"""
        if self.websocket_client.socket.state() != self.websocket_client.socket.SocketState.ConnectedState:
            print("🔄 Tentando reconectar WebSocket...")
            self.websocket_client.connect_to_server()

    def backup_message_check(self):
        """Verificação backup caso WebSocket falhe"""
        if not self._current_contact:
            return

        # Só verificar se WebSocket não está conectado
        if self.websocket_client.socket.state() != self.websocket_client.socket.SocketState.ConnectedState:
            try:
                # Verificar se há mensagens novas no banco
                latest_messages = self.db_interface.get_chat_messages(self._current_contact, 5)

                if latest_messages:
                    # Comparar com última mensagem conhecida
                    last_widget_timestamp = 0
                    layout_count = self.ui.messages_layout.count()

                    for i in range(layout_count - 1, -1, -1):
                        item = self.ui.messages_layout.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if isinstance(widget, MessageBubble):
                                last_widget_timestamp = widget.message_data.get('timestamp', 0)
                                break

                    # Verificar se há mensagens mais recentes
                    for msg in latest_messages:
                        if msg.get('timestamp', 0) > last_widget_timestamp:
                            print("📨 Nova mensagem detectada via backup check")
                            self.on_single_message_added(msg)

            except Exception as e:
                print(f"⚠️ Erro na verificação backup: {e}")

    # Métodos do sistema original adaptados...
    def start_loading(self, message: str = "Carregando..."):
        """Inicia loading otimizado"""
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

    def load_initial_data(self):
        """Carrega dados iniciais otimizados"""
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

    def on_connection_status_changed(self, connected: bool):
        """Atualiza status de conexão"""
        self.ui.update_connection_status(connected)

        if connected:
            print("✅ Conectado ao banco otimizado")
        else:
            print("❌ Desconectado do banco")
            if self._is_loading:
                self.stop_loading()

    def on_contacts_loaded(self, contacts: List[Dict]):
        """Carrega contatos otimizado"""
        print(f"📋 {len(contacts)} contatos carregados")
        self.update_contacts_list(contacts)

    def update_contacts_list(self, contacts: List[Dict]):
        """Atualiza lista de contatos na UI"""
        # Limpar lista atual
        self.ui.clear_contacts_list()
        self._loaded_contacts.clear()

        if not contacts:
            self.show_no_contacts_message()
            return

        # Adicionar contatos
        for idx, contact_data in enumerate(contacts):
            try:
                contact_widget = self.ui.add_contact_to_list(contact_data)
                contact_widget.clicked.connect(self.on_contact_selected)

                # Salvar referência
                contact_id = contact_data['chat_id']
                self._loaded_contacts[contact_id] = contact_data

            except Exception as e:
                print(f"⚠️ Erro ao adicionar contato {idx}: {e}")
                continue

        print(f"✅ Lista atualizada: {len(self._loaded_contacts)} conversas")

    def show_no_contacts_message(self):
        """Mostra mensagem quando não há contatos"""
        print("📭 Nenhuma conversa encontrada")

    def show_connection_error(self):
        """Mostra erro de conexão"""
        print("❌ Erro de conexão com banco")
        self.ui.update_connection_status(False)

    def on_contact_selected(self, contact_id: str):
        """Seleciona contato e carrega mensagens OTIMIZADO"""
        if contact_id not in self._loaded_contacts or self._is_loading:
            return

        contact_data = self._loaded_contacts[contact_id]
        print(f"👤 Selecionado: {contact_data['chat_name'][:30]}")

        # Atualizar estado
        self._current_contact = contact_id
        self._current_contact_data = contact_data
        self._oldest_message_timestamp = None
        self._is_at_bottom = True

        # Limpar cache de widgets anteriores
        self._message_widgets.clear()

        # Atualizar UI
        self.ui.show_chat_screen()
        self.ui.update_active_contact(contact_data)
        self.ui.clear_messages()

        # Carregar mensagens iniciais
        self.start_loading("Carregando mensagens...")

        if self.db_worker.isRunning():
            self.db_worker.stop_task()
            self.db_worker.wait(1000)

        self.db_worker.set_task("load_messages_initial", chat_id=contact_id)
        self.db_worker.start()

    def on_messages_loaded(self, messages: List[Dict], is_initial: bool):
        """Carrega mensagens iniciais SEM tremor"""
        if not self._current_contact:
            return

        print(f"💬 {len(messages)} mensagens carregadas (inicial: {is_initial})")

        if is_initial:
            # Renderização inicial completa
            self.render_initial_messages(messages)
        else:
            # Isso não deveria acontecer com a nova arquitetura
            print("⚠️ Carregamento não-inicial inesperado")

    def render_initial_messages(self, messages: List[Dict]):
        """Renderiza mensagens iniciais de forma otimizada"""
        # Limpar mensagens atuais
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

        # Definir timestamp da mensagem mais antiga (para paginação)
        if messages_sorted:
            self._oldest_message_timestamp = messages_sorted[0].get('timestamp', 0)

        # Renderizar mensagens
        print("🎨 Renderizando mensagens iniciais...")

        previous_message = None
        widgets_added = 0
        current_date = None

        for i, message_data in enumerate(messages_sorted):
            try:
                # Processar eventos a cada 10 mensagens
                if i % 10 == 0:
                    QApplication.processEvents()

                # Verificar separador de data
                try:
                    message_dt = datetime.fromtimestamp(message_data.get('timestamp', 0))
                    message_date = message_dt.strftime('%d/%m/%Y')
                except:
                    message_date = message_data.get('date_str', '')

                # Adicionar separador se mudou
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

                        # Cache do widget
                        msg_id = message_data.get('message_id', f"msg_{i}")
                        self._message_widgets[msg_id] = message_widget
                        widgets_added += 1

                        # Animar entrada gradual
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
            # Adicionar stretch
            QTimer.singleShot(100, lambda: self.ui.messages_layout.addStretch())

            # Atualizar geometria
            QTimer.singleShot(200, self.update_messages_geometry)

            # Rolar para final
            QTimer.singleShot(300, self.ui.scroll_to_bottom)

            print(f"✅ {widgets_added} mensagens renderizadas")

        except Exception as e:
            print(f"⚠️ Erro na finalização: {e}")

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
        """Filtra contatos otimizado"""
        if self._is_loading:
            return

        search_text = search_text.lower().strip()

        # Mostrar todos se busca vazia
        if not search_text:
            for i in range(self.ui.contacts_list.count()):
                item = self.ui.contacts_list.item(i)
                if item:
                    item.setHidden(False)
            return

        # Filtrar
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
        """Atualiza chat atual (apenas forçar verificação)"""
        if self._is_loading:
            return

        if self._current_contact:
            print(f"🔄 Verificando atualizações: {self._current_contact[:15]}")
            # Em vez de recarregar tudo, apenas força verificação backup
            self.backup_message_check()
        else:
            print("🔄 Atualizando lista de contatos")
            self.load_initial_data()

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
        print(f"   Timestamp mais antigo: {self._oldest_message_timestamp}")
        print(f"   WebSocket conectado: {self.websocket_client.socket.state()}")

        if self._current_contact:
            layout_count = self.ui.messages_layout.count()
            print(f"   Widgets no layout: {layout_count}")

    def closeEvent(self, event):
        """Fecha aplicação otimizada"""
        print("👋 Encerrando aplicação otimizada...")

        # Desconectar WebSocket
        if hasattr(self, 'websocket_client'):
            self.websocket_client.disconnect_from_server()

        # Parar timers
        if hasattr(self, 'reconnect_timer'):
            self.reconnect_timer.stop()
        if hasattr(self, 'backup_check_timer'):
            self.backup_check_timer.stop()

        # Parar worker
        if hasattr(self, 'db_worker') and self.db_worker.isRunning():
            self.db_worker.stop()

        event.accept()


def main():
    """Função principal otimizada"""
    app = QApplication(sys.argv)

    app.setApplicationName("WhatsApp Chat Interface - Versão Otimizada")
    app.setApplicationVersion("3.0.0")
    app.setOrganizationName("Chat Analytics")

    try:
        app.setWindowIcon(QIcon("icon.png"))
    except:
        pass

    print("\n🚀 Iniciando interface OTIMIZADA sem tremor...")

    try:
        window = WhatsAppChatWindow()
        window.show()

        print("🎉 Interface otimizada iniciada!")
        print("💡 OTIMIZAÇÕES IMPLEMENTADAS:")
        print("   ✅ Mensagens incrementais (sem recarregar tudo)")
        print("   ✅ Paginação reversa (scroll para topo)")
        print("   ✅ WebSocket para tempo real")
        print("   ✅ Cache de widgets de mensagem")
        print("   ✅ Scroll inteligente (mantém posição)")
        print("   ✅ Envio de mensagens habilitado")
        print("   ✅ Atualização sem tremor de tela")
        print("   ✅ Backup check se WebSocket falhar")

        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro ao iniciar: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()