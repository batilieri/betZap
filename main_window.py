#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Janela principal do chat fofo WhatsApp
Integração completa com banco de dados em tempo real
"""

import sys
import os
from typing import Dict, List, Optional
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon

# Importar nossos módulos
from ui.main_window_ui import MainWindowUI, ContactItemWidget
from ui.chat_widget import MessageRenderer, MessageBubble
from database import ChatDatabaseInterface


class DatabaseWorker(QThread):
    """Worker thread para operações do banco de dados"""

    # Sinais para comunicação com a UI
    contacts_loaded = pyqtSignal(list)
    messages_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool)

    def __init__(self, db_interface: ChatDatabaseInterface):
        super().__init__()
        self.db_interface = db_interface
        self.current_task = None
        self.task_params = {}
        self.is_running = True

    def set_task(self, task_name: str, **params):
        """Define a tarefa a ser executada"""
        self.current_task = task_name
        self.task_params = params

    def run(self):
        """Executa a tarefa atual"""
        try:
            if not self.db_interface.is_connected():
                self.connection_status_changed.emit(False)
                self.error_occurred.emit("Banco de dados não conectado")
                return

            self.connection_status_changed.emit(True)

            if self.current_task == "load_contacts":
                contacts = self.db_interface.get_contacts_list(50)
                self.contacts_loaded.emit(contacts)

            elif self.current_task == "load_messages":
                contact_id = self.task_params.get('contact_id')
                if contact_id:
                    messages = self.db_interface.get_chat_messages(contact_id, 100)
                    self.messages_loaded.emit(messages)
                else:
                    self.error_occurred.emit("ID do contato não fornecido")

        except Exception as e:
            self.error_occurred.emit(f"Erro na operação: {str(e)}")

    def stop(self):
        """Para o worker thread"""
        self.is_running = False
        self.quit()
        self.wait()


class WhatsAppChatWindow(QMainWindow):
    """Janela principal do chat fofo"""

    def __init__(self):
        super().__init__()

        # Inicializar banco de dados
        self.db_interface = ChatDatabaseInterface()

        # Configurar UI
        self.ui = MainWindowUI(self)

        # Worker thread para banco
        self.db_worker = DatabaseWorker(self.db_interface)
        self.setup_database_connections()

        # Estado atual
        self.current_contact = None
        self.current_contact_data = None
        self.loaded_contacts = {}

        # Timer para atualizações automáticas
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.refresh_timer.start(30000)  # A cada 30 segundos

        # Conectar sinais da UI
        self.setup_ui_connections()

        # Carregar dados iniciais
        self.load_initial_data()

    def setup_database_connections(self):
        """Configura conexões com o worker do banco"""
        self.db_worker.contacts_loaded.connect(self.on_contacts_loaded)
        self.db_worker.messages_loaded.connect(self.on_messages_loaded)
        self.db_worker.error_occurred.connect(self.on_database_error)
        self.db_worker.connection_status_changed.connect(self.on_connection_status_changed)

    def setup_ui_connections(self):
        """Configura conexões da interface"""
        # Botão de refresh no cabeçalho do chat
        self.ui.refresh_btn.clicked.connect(self.refresh_current_chat)

        # Busca de contatos
        self.ui.search_input.textChanged.connect(self.filter_contacts)

        # Atalho de debug (Ctrl+D)
        from PyQt6.QtGui import QShortcut, QKeySequence
        debug_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        debug_shortcut.activated.connect(self.show_debug_info)

    def load_initial_data(self):
        """Carrega dados iniciais"""
        print("📥 Carregando lista de contatos...")
        self.ui.show_welcome_screen()

        if self.db_interface.is_connected():
            self.db_worker.set_task("load_contacts")
            self.db_worker.start()
        else:
            QMessageBox.warning(self, "Erro de Conexão",
                                "Não foi possível conectar ao banco de dados.\n"
                                "Verifique se o arquivo existe em: backend/banco/whatsapp_webhook_realtime.db")

    def on_connection_status_changed(self, connected: bool):
        """Atualiza status de conexão na UI"""
        self.ui.update_connection_status(connected)

        if connected:
            print("✅ Conectado ao banco de dados")
        else:
            print("❌ Desconectado do banco de dados")

    def on_contacts_loaded(self, contacts: List[Dict]):
        """Chamado quando contatos são carregados"""
        print(f"📋 {len(contacts)} contatos carregados")

        # Limpar lista atual
        self.ui.clear_contacts_list()
        self.loaded_contacts.clear()

        # Adicionar contatos à lista
        for contact_data in contacts:
            contact_widget = self.ui.add_contact_to_list(contact_data)
            contact_widget.clicked.connect(self.on_contact_selected)

            # Salvar referência
            contact_id = contact_data['contact_id']
            self.loaded_contacts[contact_id] = contact_data

        print("✅ Lista de contatos atualizada")

    def on_contact_selected(self, contact_id: str):
        """Chamado quando um contato é selecionado"""
        if contact_id not in self.loaded_contacts:
            print(f"⚠️ Contato {contact_id} não encontrado na lista")
            return

        contact_data = self.loaded_contacts[contact_id]

        print(f"👤 Contato selecionado: {contact_data['contact_name']} ({contact_id})")

        # Atualizar estado atual
        self.current_contact = contact_id
        self.current_contact_data = contact_data

        # Atualizar UI
        self.ui.show_chat_screen()
        self.ui.update_active_contact(contact_data)
        self.ui.clear_messages()

        # Carregar mensagens
        print(f"📨 Carregando mensagens do chat...")
        self.db_worker.set_task("load_messages", contact_id=contact_id)

        # Aguardar thread anterior terminar se necessário
        if self.db_worker.isRunning():
            self.db_worker.wait()

        self.db_worker.start()

    def on_messages_loaded(self, messages: List[Dict]):
        """Chamado quando mensagens são carregadas"""
        if not self.current_contact:
            return

        print(f"💬 {len(messages)} mensagens carregadas para {self.current_contact}")

        # Limpar mensagens atuais
        self.ui.clear_messages()

        if not messages:
            # Nenhuma mensagem encontrada
            self.add_system_message("Nenhuma mensagem encontrada com este contato.")
            return

        # Renderizar mensagens com separadores de data
        previous_message = None

        for i, message_data in enumerate(messages):
            print(f"  Processando mensagem {i + 1}: {message_data.get('content', '')[:50]}...")

            # Verificar se precisa de separador de data
            if MessageRenderer.should_show_date_separator(message_data, previous_message):
                date_str = message_data.get('date_str', '')
                if date_str:
                    formatted_date = MessageRenderer.format_date_separator(date_str)
                    date_separator = MessageRenderer.create_date_separator(formatted_date)
                    self.add_widget_to_chat(date_separator)
                    print(f"    + Separador de data: {formatted_date}")

            # Criar e adicionar mensagem
            try:
                message_widget = MessageRenderer.create_message_widget(message_data)
                if message_widget:
                    self.add_widget_to_chat(message_widget)
                    print(f"    + Mensagem adicionada: {type(message_widget).__name__}")

                    # Animar entrada se for MessageBubble
                    if isinstance(message_widget, MessageBubble):
                        QTimer.singleShot(50 * i, message_widget.animate_in)
                else:
                    print(f"    ! Falha ao criar widget da mensagem")
            except Exception as e:
                print(f"    ❌ Erro ao criar mensagem: {e}")
                continue

            previous_message = message_data

        # Adicionar stretch no final para empurrar mensagens para cima
        self.ui.messages_layout.addStretch()

        # Atualizar geometria e rolar para o final
        self.ui.messages_widget.updateGeometry()
        self.ui.messages_scroll.updateGeometry()

        # Rolar para o final após um pequeno delay
        QTimer.singleShot(200, self.ui.scroll_to_bottom)

        print(f"✅ {len(messages)} mensagens renderizadas na interface")

    def on_database_error(self, error_message: str):
        """Chamado quando ocorre erro no banco"""
        print(f"❌ Erro no banco: {error_message}")

        # Mostrar erro na UI se for crítico
        if "conectar" in error_message.lower() or "banco" in error_message.lower():
            QMessageBox.critical(self, "Erro do Banco de Dados",
                                 f"Erro ao acessar banco de dados:\n{error_message}")

    def add_widget_to_chat(self, widget):
        """Adiciona widget à área de mensagens"""
        # Garantir que o widget seja visível
        widget.setVisible(True)
        widget.show()

        # Adicionar ao layout
        self.ui.messages_layout.addWidget(widget)

        # Forçar atualização do layout
        self.ui.messages_widget.updateGeometry()
        self.ui.messages_scroll.updateGeometry()

        # Processar eventos pendentes
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

    def add_system_message(self, message: str):
        """Adiciona mensagem do sistema"""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        system_label = QLabel(message)
        system_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        system_label.setFont(QFont('Segoe UI', 10))
        system_label.setMinimumHeight(40)  # Altura mínima
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

        # Garantir visibilidade
        system_label.setVisible(True)
        system_label.show()

        self.add_widget_to_chat(system_label)
        print(f"📝 Mensagem do sistema adicionada: {message}")

    def filter_contacts(self, search_text: str):
        """Filtra contatos baseado no texto de busca"""
        search_text = search_text.lower().strip()

        # Se busca vazia, mostrar todos
        if not search_text:
            for i in range(self.ui.contacts_list.count()):
                item = self.ui.contacts_list.item(i)
                item.setHidden(False)
            return

        # Filtrar contatos
        for i in range(self.ui.contacts_list.count()):
            item = self.ui.contacts_list.item(i)
            widget = self.ui.contacts_list.itemWidget(item)

            if isinstance(widget, ContactItemWidget):
                contact_data = widget.contact_data
                name = contact_data.get('contact_name', '').lower()
                contact_id = contact_data.get('contact_id', '').lower()

                # Verificar se corresponde à busca
                should_show = (search_text in name or
                               search_text in contact_id or
                               search_text in contact_data.get('last_message', '').lower())

                item.setHidden(not should_show)

    def refresh_current_chat(self):
        """Atualiza o chat atual"""
        if self.current_contact:
            print(f"🔄 Atualizando chat: {self.current_contact}")

            # Parar worker se estiver rodando
            if self.db_worker.isRunning():
                print("⏳ Aguardando thread anterior...")
                self.db_worker.wait()

            # Carregar mensagens novamente
            self.db_worker.set_task("load_messages", contact_id=self.current_contact)
            self.db_worker.start()
        else:
            # Atualizar lista de contatos
            print("🔄 Atualizando lista de contatos")

            # Parar worker se estiver rodando
            if self.db_worker.isRunning():
                print("⏳ Aguardando thread anterior...")
                self.db_worker.wait()

            self.db_worker.set_task("load_contacts")
            self.db_worker.start()

    def auto_refresh(self):
        """Atualização automática periódica"""
        # Só atualizar se não estiver fazendo outra operação
        if not self.db_worker.isRunning():
            # Se tem chat ativo, atualizar mensagens
            if self.current_contact:
                print("🔄 Auto-refresh: atualizando mensagens")
                self.refresh_current_chat()
            else:
                # Senão, atualizar lista de contatos
                print("🔄 Auto-refresh: atualizando contatos")
                self.load_initial_data()
        else:
            print("⏳ Auto-refresh pulado - thread ocupada")

    def show_debug_info(self):
        """Mostra informações de debug"""
        if self.current_contact:
            layout_count = self.ui.messages_layout.count()
            print(f"🔍 DEBUG INFO:")
            print(f"   Contato atual: {self.current_contact}")
            print(f"   Widgets no layout: {layout_count}")
            print(f"   Área de mensagens visível: {self.ui.messages_widget.isVisible()}")
            print(f"   Área de scroll visível: {self.ui.messages_scroll.isVisible()}")

            # Listar widgets no layout
            for i in range(layout_count):
                item = self.ui.messages_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    print(f"   Widget {i}: {type(widget).__name__} - Visível: {widget.isVisible()}")
        else:
            print("🔍 DEBUG: Nenhum contato selecionado")

    def show_database_stats(self):
        """Mostra estatísticas do banco de dados"""
        stats = self.db_interface.get_database_stats()

        if stats:
            stats_text = f"""
📊 Estatísticas do Banco de Dados:

📁 Arquivo: {stats.get('database_path', 'N/A')}
💾 Tamanho: {stats.get('database_size_mb', 0)} MB
📨 Total de eventos: {stats.get('total_events', 0):,}
👥 Total de remetentes: {stats.get('total_senders', 0):,}
💬 Total de chats: {stats.get('total_chats', 0):,}

📅 Primeira mensagem: {stats.get('first_message_date', 'N/A')}
🕐 Última mensagem: {stats.get('last_message_date', 'N/A')}
            """

            QMessageBox.information(self, "Estatísticas do Banco", stats_text)
        else:
            QMessageBox.warning(self, "Erro", "Não foi possível obter estatísticas do banco")

    def closeEvent(self, event):
        """Evento de fechamento da janela"""
        print("👋 Encerrando aplicação...")

        # Parar timer
        self.refresh_timer.stop()

        # Parar worker thread
        if self.db_worker.isRunning():
            self.db_worker.stop()

        event.accept()


def main():
    """Função principal"""
    # Criar aplicação
    app = QApplication(sys.argv)

    # Configurar aplicação
    app.setApplicationName("WhatsApp Chat Interface")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Chat Analytics")

    # Configurar ícone se disponível
    try:
        app.setWindowIcon(QIcon("icon.png"))
    except:
        pass

    # Verificar se arquivos necessários existem
    required_files = [
        os.path.join('backend', 'banco', 'database_manager_updated.py'),
        os.path.join('backend', 'banco', 'models_updated.py')
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("❌ Arquivos necessários não encontrados:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n📁 Estrutura esperada:")
        print("   projeto/")
        print("   ├── main_window.py")
        print("   ├── database.py")
        print("   ├── ui/")
        print("   │   ├── main_window_ui.py")
        print("   │   └── chat_widget.py")
        print("   └── backend/")
        print("       └── banco/")
        print("           ├── models_updated.py")
        print("           ├── database_manager_updated.py")
        print("           └── whatsapp_webhook_realtime.db")

        # Ainda assim tenta executar
        print("\n⚠️ Tentando executar mesmo assim...")

    # Criar e mostrar janela principal
    try:
        window = WhatsAppChatWindow()
        window.show()

        print("🎉 Interface do chat iniciada!")
        print("💡 Recursos disponíveis:")
        print("   - Lista de contatos com busca")
        print("   - Visualização de mensagens por contato")
        print("   - Design fofo com cores pastéis")
        print("   - Atualização automática a cada 30 segundos")
        print("   - Suporte a todos os tipos de mensagem")
        print("\n📝 TODO - Funcionalidades futuras:")
        print("   - Envio de mensagens")
        print("   - Anexo de arquivos")
        print("   - Notificações de novas mensagens")

        # Executar aplicação
        sys.exit(app.exec())

    except Exception as e:
        print(f"❌ Erro ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

# =============================================================================
# 🎨 INTERFACE DE CHAT FOFA - WHATSAPP
# =============================================================================
#
# 📋 ARQUIVOS NECESSÁRIOS:
# - main_window.py (este arquivo - controlador principal)
# - database.py (integração com banco)
# - ui/main_window_ui.py (layout da interface)
# - ui/chat_widget.py (balões de mensagem fofos)
# - backend/banco/database_manager_updated.py (gerenciador do banco)
# - backend/banco/models_updated.py (modelos do banco)
# - backend/banco/whatsapp_webhook_realtime.db (banco SQLite)
#
# 🚀 COMO EXECUTAR:
# python main_window.py
#
# 🎯 RECURSOS IMPLEMENTADOS:
# ✅ Interface fofa com cores pastéis
# ✅ Lista de contatos com busca
# ✅ Balões de mensagem estilo Messenger
# ✅ Integração completa com banco SQLite
# ✅ Suporte a todos os tipos de mensagem
# ✅ Separadores de data automáticos
# ✅ Atualização automática
# ✅ Design responsivo
# ✅ Animações suaves
# ✅ Sombras e bordas arredondadas
#
# 🔮 TODO - PRÓXIMAS FUNCIONALIDADES:
# 🔲 Envio de mensagens (campo desabilitado)
# 🔲 Anexo de arquivos (botão desabilitado)
# 🔲 Notificações de novas mensagens
# 🔲 Busca dentro das mensagens
# 🔲 Export de conversas
# 🔲 Configurações de tema
#
# 🎨 DESIGN:
# - Cores pastéis (azul, rosa, verde menta)
# - Bordas arredondadas em tudo
# - Sombras suaves nos balões
# - Ícones fofos para tipos de mídia
# - Avatares coloridos baseados no nome
# - Gradientes suaves nos cabeçalhos
#
# 📱 TIPOS DE MENSAGEM SUPORTADOS:
# - 💬 Texto/emoji
# - 🏷️ Stickers
# - 📷 Imagens (com caption)
# - 🎥 Vídeos (com caption)
# - 🎵 Áudios
# - 📄 Documentos (com preview)
# - 📍 Localizações (com nome/endereço)
# - 📊 Enquetes (com opções)
#
# =============================================================================