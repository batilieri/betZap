#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente API WhatsApp para envio de mensagens
Suporte completo a texto, imagens, áudio, stickers, documentos
"""

import os
import json
import base64
import requests
from typing import Dict, List, Optional, Union
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QThread
import mimetypes


class WhatsAppAPIClient(QObject):
    """Cliente para comunicação com API do WhatsApp"""

    # Sinais para comunicação com a UI
    message_sent = pyqtSignal(dict)  # Sucesso no envio
    send_error = pyqtSignal(str)  # Erro no envio
    upload_progress = pyqtSignal(int)  # Progresso de upload

    def __init__(self, base_url: str = "http://localhost:3000", session_name: str = "default"):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.session_name = session_name
        self.session = requests.Session()

        # Headers padrão
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'WhatsApp-Chat-Interface/1.0'
        })

    def check_connection(self) -> bool:
        """Verifica se a API está acessível"""
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Erro ao verificar conexão: {e}")
            return False

    def send_text_message(self, to: str, message: str) -> Dict:
        """
        Envia mensagem de texto

        Args:
            to: Número do destinatário (formato: 5511999999999)
            message: Texto da mensagem

        Returns:
            Resposta da API
        """
        try:
            payload = {
                "session": self.session_name,
                "to": to,
                "text": message
            }

            response = self.session.post(
                f"{self.base_url}/client/sendMessage/{self.session_name}",
                json=payload,
                timeout=30
            )

            result = response.json()

            if response.status_code == 200:
                print(f"✅ Mensagem de texto enviada para {to}")
                return {"success": True, "data": result}
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                print(f"❌ Erro ao enviar texto: {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Erro na conexão: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def send_image_message(self, to: str, image_path: str, caption: str = "") -> Dict:
        """
        Envia imagem com caption opcional

        Args:
            to: Número do destinatário
            image_path: Caminho para o arquivo de imagem
            caption: Legenda opcional

        Returns:
            Resposta da API
        """
        try:
            if not os.path.exists(image_path):
                return {"success": False, "error": "Arquivo de imagem não encontrado"}

            # Verificar tipo de arquivo
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                return {"success": False, "error": "Arquivo não é uma imagem válida"}

            # Converter para base64
            with open(image_path, 'rb') as img_file:
                image_base64 = base64.b64encode(img_file.read()).decode('utf-8')

            # Obter nome do arquivo
            filename = os.path.basename(image_path)

            payload = {
                "session": self.session_name,
                "to": to,
                "image": image_base64,
                "fileName": filename,
                "caption": caption
            }

            response = self.session.post(
                f"{self.base_url}/client/sendFile/{self.session_name}",
                json=payload,
                timeout=60
            )

            result = response.json()

            if response.status_code == 200:
                print(f"✅ Imagem enviada para {to}")
                return {"success": True, "data": result}
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                print(f"❌ Erro ao enviar imagem: {error_msg}")
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Erro ao enviar imagem: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def send_audio_message(self, to: str, audio_path: str) -> Dict:
        """
        Envia mensagem de áudio

        Args:
            to: Número do destinatário
            audio_path: Caminho para o arquivo de áudio

        Returns:
            Resposta da API
        """
        try:
            if not os.path.exists(audio_path):
                return {"success": False, "error": "Arquivo de áudio não encontrado"}

            # Verificar tipo de arquivo
            mime_type, _ = mimetypes.guess_type(audio_path)
            if not mime_type or not mime_type.startswith('audio/'):
                return {"success": False, "error": "Arquivo não é um áudio válido"}

            # Converter para base64
            with open(audio_path, 'rb') as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode('utf-8')

            filename = os.path.basename(audio_path)

            payload = {
                "session": self.session_name,
                "to": to,
                "audio": audio_base64,
                "fileName": filename
            }

            response = self.session.post(
                f"{self.base_url}/client/sendFile/{self.session_name}",
                json=payload,
                timeout=60
            )

            result = response.json()

            if response.status_code == 200:
                print(f"✅ Áudio enviado para {to}")
                return {"success": True, "data": result}
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Erro ao enviar áudio: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def send_document_message(self, to: str, document_path: str, filename: str = None) -> Dict:
        """
        Envia documento

        Args:
            to: Número do destinatário
            document_path: Caminho para o documento
            filename: Nome personalizado do arquivo

        Returns:
            Resposta da API
        """
        try:
            if not os.path.exists(document_path):
                return {"success": False, "error": "Documento não encontrado"}

            # Converter para base64
            with open(document_path, 'rb') as doc_file:
                document_base64 = base64.b64encode(doc_file.read()).decode('utf-8')

            file_name = filename or os.path.basename(document_path)

            payload = {
                "session": self.session_name,
                "to": to,
                "document": document_base64,
                "fileName": file_name
            }

            response = self.session.post(
                f"{self.base_url}/client/sendFile/{self.session_name}",
                json=payload,
                timeout=60
            )

            result = response.json()

            if response.status_code == 200:
                print(f"✅ Documento enviado para {to}")
                return {"success": True, "data": result}
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Erro ao enviar documento: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def send_sticker_message(self, to: str, sticker_path: str) -> Dict:
        """
        Envia sticker/figurinha

        Args:
            to: Número do destinatário
            sticker_path: Caminho para o sticker (WebP)

        Returns:
            Resposta da API
        """
        try:
            if not os.path.exists(sticker_path):
                return {"success": False, "error": "Sticker não encontrado"}

            # Converter para base64
            with open(sticker_path, 'rb') as sticker_file:
                sticker_base64 = base64.b64encode(sticker_file.read()).decode('utf-8')

            payload = {
                "session": self.session_name,
                "to": to,
                "sticker": sticker_base64
            }

            response = self.session.post(
                f"{self.base_url}/client/sendFile/{self.session_name}",
                json=payload,
                timeout=60
            )

            result = response.json()

            if response.status_code == 200:
                print(f"✅ Sticker enviado para {to}")
                return {"success": True, "data": result}
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Erro ao enviar sticker: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def send_location_message(self, to: str, latitude: float, longitude: float, name: str = "") -> Dict:
        """
        Envia localização

        Args:
            to: Número do destinatário
            latitude: Latitude
            longitude: Longitude
            name: Nome do local (opcional)

        Returns:
            Resposta da API
        """
        try:
            payload = {
                "session": self.session_name,
                "to": to,
                "lat": latitude,
                "lng": longitude,
                "loc": name
            }

            response = self.session.post(
                f"{self.base_url}/client/sendLocation/{self.session_name}",
                json=payload,
                timeout=30
            )

            result = response.json()

            if response.status_code == 200:
                print(f"✅ Localização enviada para {to}")
                return {"success": True, "data": result}
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Erro ao enviar localização: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

    def get_session_status(self) -> Dict:
        """Verifica status da sessão"""
        try:
            response = self.session.get(
                f"{self.base_url}/client/getSessionState/{self.session_name}",
                timeout=10
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": "Erro ao verificar sessão"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_profile_picture(self, contact_id: str) -> Dict:
        """Obtém foto de perfil do contato"""
        try:
            payload = {
                "session": self.session_name,
                "number": contact_id
            }

            response = self.session.post(
                f"{self.base_url}/client/getProfilePicFromServer/{self.session_name}",
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": "Erro ao obter foto"}

        except Exception as e:
            return {"success": False, "error": str(e)}


class MessageSender(QThread):
    """Thread para envio de mensagens sem bloquear UI"""

    # Sinais
    message_sent = pyqtSignal(dict, dict)  # mensagem_data, resposta_api
    send_error = pyqtSignal(str)
    upload_progress = pyqtSignal(int)

    def __init__(self, api_client: WhatsAppAPIClient):
        super().__init__()
        self.api_client = api_client
        self.message_queue = []
        self._stop_requested = False

    def add_message_to_queue(self, message_data: Dict):
        """Adiciona mensagem à fila de envio"""
        self.message_queue.append(message_data)

        if not self.isRunning():
            self.start()

    def run(self):
        """Processa fila de mensagens"""
        while self.message_queue and not self._stop_requested:
            try:
                message_data = self.message_queue.pop(0)

                # Emitir progresso
                self.upload_progress.emit(0)

                # Processar mensagem baseado no tipo
                message_type = message_data.get('type', 'text')
                to = message_data.get('to', '')

                result = None

                if message_type == 'text':
                    result = self.api_client.send_text_message(
                        to, message_data.get('content', '')
                    )

                elif message_type == 'image':
                    result = self.api_client.send_image_message(
                        to,
                        message_data.get('file_path', ''),
                        message_data.get('caption', '')
                    )

                elif message_type == 'audio':
                    result = self.api_client.send_audio_message(
                        to, message_data.get('file_path', '')
                    )

                elif message_type == 'document':
                    result = self.api_client.send_document_message(
                        to,
                        message_data.get('file_path', ''),
                        message_data.get('filename', None)
                    )

                elif message_type == 'sticker':
                    result = self.api_client.send_sticker_message(
                        to, message_data.get('file_path', '')
                    )

                elif message_type == 'location':
                    result = self.api_client.send_location_message(
                        to,
                        message_data.get('latitude', 0),
                        message_data.get('longitude', 0),
                        message_data.get('location_name', '')
                    )

                # Emitir progresso completo
                self.upload_progress.emit(100)

                if result and result.get('success'):
                    self.message_sent.emit(message_data, result)
                else:
                    error = result.get('error', 'Erro desconhecido') if result else 'Falha na comunicação'
                    self.send_error.emit(error)

            except Exception as e:
                self.send_error.emit(f"Erro no envio: {str(e)}")

    def stop_sending(self):
        """Para o thread de envio"""
        self._stop_requested = True
        self.quit()
        self.wait()


# Utilitários para preparação de mensagens
class MessagePreparator:
    """Classe para preparar mensagens antes do envio"""

    @staticmethod
    def prepare_text_message(to: str, text: str) -> Dict:
        """Prepara mensagem de texto"""
        return {
            'type': 'text',
            'to': to,
            'content': text,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def prepare_image_message(to: str, image_path: str, caption: str = "") -> Dict:
        """Prepara mensagem de imagem"""
        return {
            'type': 'image',
            'to': to,
            'file_path': image_path,
            'caption': caption,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def prepare_audio_message(to: str, audio_path: str) -> Dict:
        """Prepara mensagem de áudio"""
        return {
            'type': 'audio',
            'to': to,
            'file_path': audio_path,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def prepare_document_message(to: str, document_path: str, filename: str = None) -> Dict:
        """Prepara mensagem de documento"""
        return {
            'type': 'document',
            'to': to,
            'file_path': document_path,
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def prepare_sticker_message(to: str, sticker_path: str) -> Dict:
        """Prepara mensagem de sticker"""
        return {
            'type': 'sticker',
            'to': to,
            'file_path': sticker_path,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def prepare_location_message(to: str, lat: float, lng: float, name: str = "") -> Dict:
        """Prepara mensagem de localização"""
        return {
            'type': 'location',
            'to': to,
            'latitude': lat,
            'longitude': lng,
            'location_name': name,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def format_phone_number(phone: str) -> str:
        """Formata número de telefone para o padrão da API"""
        # Remove caracteres não numéricos
        numbers = ''.join(filter(str.isdigit, phone))

        # Adiciona código do país se necessário
        if len(numbers) == 11 and numbers.startswith('11'):
            return f"55{numbers}"
        elif len(numbers) == 10:
            return f"55{numbers}"
        elif len(numbers) == 13 and numbers.startswith('55'):
            return numbers

        return numbers

    @staticmethod
    def validate_file_for_whatsapp(file_path: str, file_type: str) -> Dict:
        """Valida arquivo para envio no WhatsApp"""
        if not os.path.exists(file_path):
            return {"valid": False, "error": "Arquivo não encontrado"}

        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)

        # Limites do WhatsApp
        limits = {
            'image': 16 * 1024 * 1024,  # 16MB
            'audio': 16 * 1024 * 1024,  # 16MB
            'document': 100 * 1024 * 1024,  # 100MB
            'sticker': 500 * 1024  # 500KB
        }

        # Verificar tamanho
        if file_type in limits and file_size > limits[file_type]:
            return {
                "valid": False,
                "error": f"Arquivo muito grande. Máximo: {limits[file_type] // (1024 * 1024)}MB"
            }

        # Verificar tipo MIME
        valid_types = {
            'image': ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
            'audio': ['audio/mpeg', 'audio/mp4', 'audio/ogg', 'audio/wav', 'audio/aac'],
            'document': None,  # Aceita qualquer tipo
            'sticker': ['image/webp']
        }

        if file_type in valid_types and valid_types[file_type]:
            if mime_type not in valid_types[file_type]:
                return {
                    "valid": False,
                    "error": f"Tipo de arquivo não suportado: {mime_type}"
                }

        return {"valid": True, "mime_type": mime_type, "size": file_size}


# Exemplo de uso da API
if __name__ == "__main__":
    # Teste básico da API
    api_client = WhatsAppAPIClient()

    # Verificar conexão
    if api_client.check_connection():
        print("✅ API conectada com sucesso")

        # Teste de envio de texto
        result = api_client.send_text_message("5511999999999", "Teste da API! 👋")
        print(f"Resultado: {result}")

    else:
        print("❌ Falha na conexão com a API")
        print("💡 Certifique-se de que o servidor está rodando em http://localhost:3000")