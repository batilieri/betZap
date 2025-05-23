"""
Cliente específico para integração com W-API WhatsApp
Este módulo contém todas as funções específicas para a W-API
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union, Any


class WAPIClient:
    """Cliente para interação com a W-API do WhatsApp"""

    def __init__(self, base_url: str = "", token: str = "", instance_id: str = ""):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.instance_id = instance_id
        self.session = requests.Session()

        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })

    def update_credentials(self, base_url: str, token: str, instance_id: str):
        """Atualiza as credenciais da API"""
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.instance_id = instance_id

        self.session.headers.update({
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })

    def get_instance_status(self) -> Tuple[bool, Dict]:
        """
        Obtém o status da instância WhatsApp

        Endpoint: GET /api/v1/instances/{instance_id}/status
        """
        try:
            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/status"
            response = self.session.get(url, timeout=15)

            if response.status_code == 200:
                data = response.json()
                return True, {
                    'status': data.get('status', 'unknown'),
                    'qr_code': data.get('qrCode', ''),
                    'connected': data.get('connected', False),
                    'phone_number': data.get('phoneNumber', ''),
                    'battery': data.get('battery', 0)
                }
            else:
                return False, {'error': f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return False, {'error': str(e)}

    def get_profile_info(self) -> Tuple[bool, Dict]:
        """
        Obtém informações do perfil

        Endpoint: GET /api/v1/instances/{instance_id}/profile
        """
        try:
            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/profile"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return True, {
                    'name': data.get('name', ''),
                    'phone': data.get('wid', {}).get('user', ''),
                    'status_text': data.get('status', ''),
                    'profile_picture': data.get('profilePictureUrl', '')
                }
            else:
                return False, {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return False, {'error': str(e)}

    def send_text_message(self, phone_number: str, message: str) -> Tuple[bool, Dict]:
        """
        Envia mensagem de texto

        Endpoint: POST /api/v1/instances/{instance_id}/client/action/send-message
        """
        try:
            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/client/action/restart"
            response = self.session.post(url, timeout=10)

            if response.status_code == 200:
                return True, {'status': 'restarted'}
            else:
                return False, {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return False, {'error': str(e)}

    def check_number_exists(self, phone_number: str) -> Tuple[bool, Dict]:
        """
        Verifica se um número tem WhatsApp

        Endpoint: GET /api/v1/instances/{instance_id}/client/action/check-number-status
        """
        try:
            if not self._validate_credentials():
                return False, {'error': 'Credenciais não configuradas'}

            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/client/action/check-number-status"

            # Limpar formatação do número
            clean_number = self._clean_phone_number(phone_number)
            params = {'number': clean_number}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return True, {
                    'exists': data.get('exists', False),
                    'number': data.get('number', clean_number),
                    'formatted_number': data.get('formattedNumber', ''),
                    'whatsapp_id': data.get('jid', '')
                }
            else:
                return False, {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return False, {'error': str(e)}

    def get_contact_info(self, phone_number: str) -> Tuple[bool, Dict]:
        """
        Obtém informações de um contato

        Endpoint: GET /api/v1/instances/{instance_id}/client/action/get-contact
        """
        try:
            if not self._validate_credentials():
                return False, {'error': 'Credenciais não configuradas'}

            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/client/action/get-contact"
            formatted_number = self._format_phone_number(phone_number)

            params = {'contactId': formatted_number}
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return True, {
                    'name': data.get('name', data.get('pushname', '')),
                    'push_name': data.get('pushname', ''),
                    'short_name': data.get('shortName', ''),
                    'number': data.get('number', ''),
                    'profile_picture': data.get('profilePicThumbObj', {}).get('eurl', ''),
                    'is_business': data.get('isBusiness', False),
                    'is_contact': data.get('isMyContact', False)
                }
            else:
                return False, {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return False, {'error': str(e)}

    def mark_message_as_read(self, chat_id: str) -> Tuple[bool, Dict]:
        """
        Marca mensagens como lidas

        Endpoint: POST /api/v1/instances/{instance_id}/client/action/mark-chat-read
        """
        try:
            if not self._validate_credentials():
                return False, {'error': 'Credenciais não configuradas'}

            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/client/action/mark-chat-read"

            payload = {'chatId': chat_id}
            response = self.session.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                return True, {'status': 'marked_as_read'}
            else:
                return False, {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return False, {'error': str(e)}

    def send_typing_indicator(self, chat_id: str, typing: bool = True) -> Tuple[bool, Dict]:
        """
        Envia indicador de digitação

        Endpoint: POST /api/v1/instances/{instance_id}/client/action/send-typing
        """
        try:
            if not self._validate_credentials():
                return False, {'error': 'Credenciais não configuradas'}

            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/client/action/send-typing"

            payload = {
                'chatId': chat_id,
                'typing': typing
            }
            response = self.session.post(url, json=payload, timeout=5)

            if response.status_code == 200:
                return True, {'status': 'typing_sent'}
            else:
                return False, {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return False, {'error': str(e)}

    def get_instance_qr_code(self) -> Tuple[bool, str]:
        """
        Obtém QR Code para conectar a instância

        Endpoint: GET /api/v1/instances/{instance_id}/qr-code
        """
        try:
            if not self._validate_credentials():
                return False, "Credenciais não configuradas"

            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/qr-code"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                qr_code = data.get('qrCode', data.get('qr', ''))
                if qr_code:
                    return True, qr_code
                else:
                    return False, "QR Code não disponível - instância pode já estar conectada"
            elif response.status_code == 404:
                return False, "Instância não encontrada"
            else:
                return False, f"HTTP {response.status_code}"

        except Exception as e:
            return False, str(e)

    def disconnect_instance(self) -> Tuple[bool, Dict]:
        """
        Desconecta a instância do WhatsApp

        Endpoint: POST /api/v1/instances/{instance_id}/client/action/logout
        """
        try:
            if not self._validate_credentials():
                return False, {'error': 'Credenciais não configuradas'}

            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/client/action/logout"
            response = self.session.post(url, timeout=10)

            if response.status_code == 200:
                return True, {'status': 'disconnected'}
            else:
                return False, {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return False, {'error': str(e)}

    def restart_instance(self) -> Tuple[bool, Dict]:
        """
        Reinicia a instância

        Endpoint: POST /api/v1/instances/{instance_id}/client/action/restart
        """
        try:
            if not self._validate_credentials():
                return False, {'error': 'Credenciais não configuradas'}

            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/client/action/restart"
            response = self.session.post(url, timeout=10)

            if response.status_code == 200:
                return True, {'status': 'restarted'}
            else:
                return False, {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return False, {'error': str(e)}

    def create_group(self, group_name: str, participants: List[str]) -> Tuple[bool, Dict]:
        """
        Cria um grupo

        Endpoint: POST /api/v1/instances/{instance_id}/client/action/create-group
        """
        try:
            if not self._validate_credentials():
                return False, {'error': 'Credenciais não configuradas'}

            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/client/action/create-group"

            # Formatar participantes
            formatted_participants = []
            for participant in participants:
                formatted_participants.append(self._format_phone_number(participant))

            payload = {
                'name': group_name,
                'participants': formatted_participants
            }

            response = self.session.post(url, json=payload, timeout=15)

            if response.status_code == 200:
                data = response.json()
                return True, {
                    'group_id': data.get('id', ''),
                    'group_name': group_name,
                    'participants_count': len(formatted_participants),
                    'participants': formatted_participants
                }
            else:
                return False, {'error': f"HTTP {response.status_code}: {response.text}"}

        except Exception as e:
            return False, {'error': str(e)}

    def get_group_info(self, group_id: str) -> Tuple[bool, Dict]:
        """
        Obtém informações de um grupo

        Endpoint: GET /api/v1/instances/{instance_id}/client/action/get-group-metadata
        """
        try:
            if not self._validate_credentials():
                return False, {'error': 'Credenciais não configuradas'}

            url = f"{self.base_url}/api/v1/instances/{self.instance_id}/client/action/get-group-metadata"
            params = {'groupId': group_id}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return True, {
                    'id': data.get('id', ''),
                    'name': data.get('subject', ''),
                    'description': data.get('desc', ''),
                    'owner': data.get('owner', ''),
                    'creation_time': data.get('creation', 0),
                    'participants': data.get('participants', []),
                    'participants_count': len(data.get('participants', [])),
                    'is_announcement': data.get('announce', False),
                    'is_restricted': data.get('restrict', False)
                }
            else:
                return False, {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            return False, {'error': str(e)}

    # ===========================================
    # MÉTODOS AUXILIARES PRIVADOS
    # ===========================================

    def _validate_credentials(self) -> bool:
        """Valida se as credenciais estão configuradas"""
        return bool(self.base_url and self.token and self.instance_id)

    def _clean_phone_number(self, phone_number: str) -> str:
        """Remove formatação do número de telefone"""
        # Remove todos os caracteres não numéricos exceto +
        import re
        cleaned = re.sub(r'[^\d+]', '', phone_number)

        # Remove + do início se presente
        if cleaned.startswith('+'):
            cleaned = cleaned[1:]

        return cleaned

    def _format_phone_number(self, phone_number: str) -> str:
        """Formata número de telefone para o padrão WhatsApp"""
        if '@c.us' in phone_number or '@g.us' in phone_number:
            return phone_number

        cleaned = self._clean_phone_number(phone_number)
        return f"{cleaned}@c.us"

    def _extract_phone_from_id(self, chat_id: str) -> str:
        """Extrai número de telefone do ID do chat"""
        if '@c.us' in chat_id:
            return chat_id.split('@')[0]
        elif '@g.us' in chat_id:
            return chat_id  # É um grupo, retorna o ID completo
        return chat_id

    def _extract_chat_name(self, chat_data: Dict) -> str:
        """Extrai nome do chat dos dados"""
        # Prioridade: name > pushname > notifyName > formattedTitle > número
        name = (
                chat_data.get('name') or
                chat_data.get('pushname') or
                chat_data.get('notifyName') or
                chat_data.get('formattedTitle') or
                self._extract_phone_from_id(chat_data.get('id', ''))
        )
        return str(name) if name else 'Contato'

    def _extract_last_message(self, chat_data: Dict) -> str:
        """Extrai a última mensagem do chat"""
        last_message = chat_data.get('lastMessage', {})

        if isinstance(last_message, dict):
            body = last_message.get('body', '')
            msg_type = last_message.get('type', 'text')

            # Personalizar texto baseado no tipo
            if msg_type == 'image':
                return '📷 Imagem'
            elif msg_type == 'video':
                return '🎥 Vídeo'
            elif msg_type == 'audio' or msg_type == 'ptt':
                return '🎵 Áudio'
            elif msg_type == 'document':
                return '📎 Documento'
            elif msg_type == 'location':
                return '📍 Localização'
            elif msg_type == 'contact':
                return '👤 Contato'
            elif body:
                # Limitar tamanho da mensagem
                return body[:50] + '...' if len(body) > 50 else body
            else:
                return 'Mensagem'

        return 'Sem mensagens'

    def _extract_media_url(self, message_data: Dict) -> str:
        """Extrai URL de mídia da mensagem"""
        if message_data.get('type') in ['image', 'video', 'document', 'audio']:
            return message_data.get('mediaUrl', message_data.get('url', ''))
        return ''

    def _extract_quoted_message(self, message_data: Dict) -> Optional[Dict]:
        """Extrai mensagem citada se existir"""
        quoted = message_data.get('quotedMsg', message_data.get('contextInfo', {}))

        if quoted and isinstance(quoted, dict):
            return {
                'id': quoted.get('id', ''),
                'body': quoted.get('body', ''),
                'sender': quoted.get('from', ''),
                'type': quoted.get('type', 'text')
            }

        return None

    def _format_timestamp(self, timestamp: Union[int, float]) -> str:
        """Converte timestamp para formato de hora"""
        try:
            if timestamp:
                # Verificar se é timestamp em segundos ou milissegundos
                if timestamp > 1e10:  # Provavelmente milissegundos
                    timestamp = timestamp / 1000

                return datetime.fromtimestamp(timestamp).strftime("%H:%M")
        except (ValueError, OSError):
            pass

        return "00:00"

    def validate_config(self) -> Tuple[bool, str]:
        """Valida se a configuração está completa e funcional"""
        if not self.base_url:
            return False, "URL base não configurada"
        if not self.token:
            return False, "Token não configurado"
        if not self.instance_id:
            return False, "ID da instância não configurado"

        # Validar formato da URL
        if not (self.base_url.startswith('http://') or self.base_url.startswith('https://')):
            return False, "URL base deve começar com http:// ou https://"

        # Teste básico de conectividade
        try:
            success, result = self.get_instance_status()
            if success:
                status = result.get('status', 'unknown')
                return True, f"Configuração válida - Status: {status}"
            else:
                error = result.get('error', 'Erro desconhecido')
                return False, f"Erro na validação: {error}"
        except Exception as e:
            return False, f"Erro de conectividade: {str(e)}"

    def get_api_info(self) -> Dict[str, Any]:
        """Obtém informações sobre a configuração da API"""
        return {
            'base_url': self.base_url,
            'instance_id': self.instance_id,
            'token_configured': bool(self.token),
            'token_length': len(self.token) if self.token else 0,
            'headers': dict(self.session.headers),
            'timeout': getattr(self.session, 'timeout', 30)
        }


if __name__ == "__main__":
    # Exemplo de como usar o cliente
    client = WAPIClient(
        base_url="https://api.w-api.com/v1",
        token="hov0ig4dm6Qadw7qmFdRHCuul1G15YUno",
        instance_id="LITE-YLOCZC-ZGHBVR"
    )

    # Validar configuração
    valid, message = client.validate_config()
    print(f"Configuração: {message}")

    if valid:
        # Testar status
        success, status = client.get_instance_status()
        if success:
            print(f"Status da instância: {status}")
        else:
            print(f"Erro no status: {status}")

        # Enviar mensagem de teste
        success, result = client.send_text_message("556999267344", "Olá, teste da API!")
        if success:
            print(f"Mensagem enviada: {result}")
        else:
            print(f"Erro ao enviar: {result}")

        # Obter chats
        success, chats = client.get_chats(10)
        if success:
            print(f"Encontrados {len(chats)} chats")
            for chat in chats[:3]:  # Mostrar apenas os 3 primeiros
                print(f"- {chat['name']}: {chat['last_message']}")
        else:
            print("Erro ao obter chats")
    else:
        print("Configure a API antes de usar")







