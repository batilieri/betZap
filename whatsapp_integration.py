#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integração completa da WhatsAppAPI com a interface de chat
Envio real de mensagens, arquivos e gerenciamento de erros
"""

import os
import sys
import json
import threading
import time
from typing import Dict, Optional, Callable
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox, QApplication

# Importar WhatsAppAPI
try:
    from backend.__whatsAppApi import WhatsAppAPI

    WHATSAPP_API_AVAILABLE = True
except ImportError:
    try:
        from backend.wapi.__whatsAppApi import WhatsAppAPI

        WHATSAPP_API_AVAILABLE = True
    except ImportError:
        print("⚠️ WhatsAppAPI não encontrada")
        WHATSAPP_API_AVAILABLE = False


        # Classe mock para desenvolvimento
        class WhatsAppAPI:
            def __init__(self, instance_id, api_token, base_url=""):
                self.instance_id = instance_id
                self.api_token = api_token

            def checa_status_conexao(self, api_token, id_instance):
                return "disconnected"

            def envia_mensagem_texto(self, phone, message, delay=1):
                return {"status": "mock", "message": "API não disponível"}


class WhatsAppConfig:
    """Configurações da API WhatsApp"""

    def __init__(self):
        # Configurações padrão - ALTERE AQUI SUAS CREDENCIAIS
        self.INSTANCE_ID = "3B6XIW-ZTS923-GEAY6V"  # Seu ID de instância
        self.API_TOKEN = "Q8EOH07SJkXhg4iT6Qmhz1BJdLl8nL9WF"  # Seu token da API
        self.BASE_URL = "https://api.w-api.app/v1/"

        # Carregar de arquivo de configuração se existir
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
                self.save_to_file()  # Criar arquivo padrão
        else:
            self.save_to_file()  # Criar arquivo de exemplo

    def save_to_file(self):
        """Salva configurações em arquivo JSON"""
        config = {
            'instance_id': self.INSTANCE_ID,
            'api_token': self.API_TOKEN,
            'base_url': self.BASE_URL
        }

        try:
            with open("whatsapp_config.json", 'w') as f:
                json.dump(config, f, indent=2)
            print("📄 Arquivo whatsapp_config.json criado")
        except Exception as e:
            print(f"⚠️ Erro ao salvar configurações: {e}")


class WhatsAppMessageSender(QThread):
    """Thread otimizada para envio de mensagens via WhatsApp API"""

    # Sinais
    message_sent = pyqtSignal(dict)  # Mensagem enviada com sucesso
    message_failed = pyqtSignal(str, str)  # Erro no envio (contact_id, erro)
    progress_update = pyqtSignal(int)  # Progresso (0-100)
    connection_status = pyqtSignal(bool)  # Status da conexão

    def __init__(self):
        super().__init__()

        # Configurações
        self.config = WhatsAppConfig()
        self.whatsapp_api = None

        # Fila de mensagens
        self.message_queue = []
        self.is_sending = False
        self.stop_requested = False

        # Inicializar API
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

            # Verificar conexão
            status = self.whatsapp_api.checa_status_conexao(
                self.config.API_TOKEN,
                self.config.INSTANCE_ID
            )

            connected = status == "connected"
            self.connection_status.emit(connected)

            if connected:
                print("✅ WhatsApp API conectada com sucesso")
            else:
                print("⚠️ WhatsApp API não conectada")

            return connected

        except Exception as e:
            print(f"❌ Erro ao inicializar WhatsApp API: {e}")
            self.connection_status.emit(False)
            return False

    def add_text_message(self, contact_id: str, message: str, delay: int = 1):
        """Adiciona mensagem de texto à fila"""
        message_data = {
            'type': 'text',
            'contact_id': self._format_phone_number(contact_id),
            'content': message,
            'delay': delay,
            'timestamp': datetime.now().isoformat(),
            'temp_id': f"temp_{int(time.time() * 1000)}"
        }

        self.message_queue.append(message_data)
        print(f"📝 Mensagem de texto adicionada à fila: {contact_id}")

        if not self.is_sending:
            self.start_sending()

    def add_file_message(self, contact_id: str, file_path: str, file_type: str, caption: str = ""):
        """Adiciona mensagem de arquivo à fila"""
        if not os.path.exists(file_path):
            self.message_failed.emit(contact_id, f"Arquivo não encontrado: {file_path}")
            return

        message_data = {
            'type': 'file',
            'file_type': file_type,  # 'image', 'document', 'audio', 'video'
            'contact_id': self._format_phone_number(contact_id),
            'file_path': file_path,
            'caption': caption,
            'timestamp': datetime.now().isoformat(),
            'temp_id': f"temp_{int(time.time() * 1000)}"
        }

        self.message_queue.append(message_data)
        print(f"📎 Arquivo adicionado à fila: {file_type} - {os.path.basename(file_path)}")

        if not self.is_sending:
            self.start_sending()

    def start_sending(self):
        """Inicia o envio das mensagens na fila"""
        if not self.isRunning():
            self.start()

    def run(self):
        """Processa a fila de mensagens"""
        self.is_sending = True

        while self.message_queue and not self.stop_requested:
            message_data = self.message_queue.pop(0)

            try:
                self.progress_update.emit(0)
                success = self._send_single_message(message_data)

                if success:
                    # Criar dados da mensagem enviada para a interface
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
                print(f"❌ {error_msg}")
                self.message_failed.emit(message_data['contact_id'], error_msg)

            # Pequeno delay entre mensagens
            if self.message_queue:
                time.sleep(0.5)

        self.is_sending = False
        self.progress_update.emit(0)

    def _send_single_message(self, message_data: Dict) -> bool:
        """Envia uma única mensagem"""
        if not self.whatsapp_api:
            return False

        try:
            if message_data['type'] == 'text':
                # Enviar mensagem de texto
                result = self.whatsapp_api.envia_mensagem_texto(
                    phone_number=message_data['contact_id'],
                    message=message_data['content'],
                    delay_message=message_data.get('delay', 1)
                )

            elif message_data['type'] == 'file':
                # Enviar arquivo baseado no tipo
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
                    # Tipo desconhecido, enviar como documento
                    result = self.whatsapp_api.envia_documento(
                        phone_number=contact_id,
                        file_path=file_path,
                        caption=caption
                    )

                self.progress_update.emit(75)

            else:
                print(f"⚠️ Tipo de mensagem desconhecido: {message_data['type']}")
                return False

            # Verificar resultado
            if result and isinstance(result, dict):
                # API retornou algo - considerar sucesso
                print(f"✅ Mensagem enviada: {result}")
                return True
            else:
                print(f"❌ Falha no envio: {result}")
                return False

        except Exception as e:
            print(f"❌ Erro no envio: {e}")
            return False

    def _create_sent_message_data(self, message_data: Dict) -> Dict:
        """Cria dados da mensagem enviada para a interface"""
        timestamp = int(time.time())

        # Determinar conteúdo baseado no tipo
        if message_data['type'] == 'text':
            content = message_data['content']
            message_type = 'text'
            media_data = None

        else:
            # Mensagem de arquivo
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

        return {
            'message_id': message_data['temp_id'],
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
            'contact_id': message_data['contact_id']
        }

    def _format_phone_number(self, phone: str) -> str:
        """Formata número de telefone para a API"""
        # Remover caracteres especiais
        phone_clean = ''.join(filter(str.isdigit, phone))

        # Se não começar com código do país, adicionar 55 (Brasil)
        if len(phone_clean) == 11 and not phone_clean.startswith('55'):
            phone_clean = '55' + phone_clean
        elif len(phone_clean) == 10 and not phone_clean.startswith('55'):
            phone_clean = '55' + phone_clean

        return phone_clean

    def check_connection(self) -> bool:
        """Verifica status da conexão"""
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
        """Para o envio de mensagens"""
        self.stop_requested = True
        self.message_queue.clear()
        self.is_sending = False


class WhatsAppIntegratedMessageSender(WhatsAppMessageSender):
    """Versão integrada do MessageSender com WhatsApp API real"""

    def __init__(self, db_interface=None):
        super().__init__()
        self.db_interface = db_interface

        # Timer para verificação periódica de conexão
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(30000)  # Verificar a cada 30 segundos

    def send_text_message_to_contact(self, contact_id: str, message: str):
        """Interface simplificada para envio de texto"""
        if not message.strip():
            return

        print(f"📱 Enviando texto para {contact_id}: {message[:50]}...")
        self.add_text_message(contact_id, message.strip())

    def send_file_to_contact(self, contact_id: str, file_path: str, file_type: str, caption: str = ""):
        """Interface simplificada para envio de arquivos"""
        if not os.path.exists(file_path):
            self.message_failed.emit(contact_id, f"Arquivo não encontrado: {file_path}")
            return

        print(f"📎 Enviando {file_type} para {contact_id}: {os.path.basename(file_path)}")
        self.add_file_message(contact_id, file_path, file_type, caption)

    def delete_message(self, contact_id: str, message_id: str):
        """Deleta uma mensagem"""
        if not self.whatsapp_api:
            return False

        try:
            result = self.whatsapp_api.deleta_mensagem(
                phone_number=self._format_phone_number(contact_id),
                message_ids=[message_id]
            )

            return bool(result)

        except Exception as e:
            print(f"❌ Erro ao deletar mensagem: {e}")
            return False

    def edit_message(self, contact_id: str, message_id: str, new_text: str):
        """Edita uma mensagem"""
        if not self.whatsapp_api:
            return False

        try:
            result = self.whatsapp_api.editar_mensagem(
                phone=self._format_phone_number(contact_id),
                message_id=message_id,
                new_text=new_text
            )

            return bool(result)

        except Exception as e:
            print(f"❌ Erro ao editar mensagem: {e}")
            return False

    def send_reaction(self, contact_id: str, message_id: str, reaction: str):
        """Envia reação para uma mensagem"""
        if not self.whatsapp_api:
            return False

        try:
            result = self.whatsapp_api.enviar_reacao(
                phone=self._format_phone_number(contact_id),
                message_id=message_id,
                reaction=reaction
            )

            return bool(result)

        except Exception as e:
            print(f"❌ Erro ao enviar reação: {e}")
            return False

    def remove_reaction(self, contact_id: str, message_id: str):
        """Remove reação de uma mensagem"""
        if not self.whatsapp_api:
            return False

        try:
            result = self.whatsapp_api.removerReacao(
                phone=self._format_phone_number(contact_id),
                menssagem_id=message_id,  # Nota: API usa 'menssagem_id'
                dalay=1
            )

            return bool(result)

        except Exception as e:
            print(f"❌ Erro ao remover reação: {e}")
            return False


def create_whatsapp_sender(db_interface=None):
    """Factory function para criar sender integrado"""
    if not WHATSAPP_API_AVAILABLE:
        print("⚠️ WhatsAppAPI não disponível, usando modo simulação")

    return WhatsAppIntegratedMessageSender(db_interface)


# Exemplo de uso e teste
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Criar sender
    sender = create_whatsapp_sender()


    def on_message_sent(message_data):
        print(f"✅ Mensagem enviada: {message_data}")


    def on_message_failed(contact_id, error):
        print(f"❌ Falha no envio para {contact_id}: {error}")


    def on_connection_status(connected):
        print(f"🔗 Status conexão: {'Conectado' if connected else 'Desconectado'}")


    # Conectar sinais
    sender.message_sent.connect(on_message_sent)
    sender.message_failed.connect(on_message_failed)
    sender.connection_status.connect(on_connection_status)

    # Verificar conexão
    sender.check_connection()

    print("🧪 Teste da integração WhatsApp API")
    print("📋 Configurações carregadas:")
    print(f"   Instance ID: {sender.config.INSTANCE_ID}")
    print(f"   API Token: {sender.config.API_TOKEN[:10]}...")
    print(f"   Base URL: {sender.config.BASE_URL}")

    # Teste básico (descomente para testar)
    # sender.send_text_message_to_contact("5569993291093", "Teste de integração")

    sys.exit(app.exec())