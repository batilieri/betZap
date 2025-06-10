
# -*- coding: utf-8 -*-
"""
Interface MELHORADA para o banco de dados WhatsApp
MELHORIAS: Nomes dos contatos, barra de progresso, tempo real
"""

import sys
import os
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict

# Adicionar caminho do backend
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'banco')
sys.path.insert(0, backend_path)

try:
    from database_manager_updated import WhatsAppDatabaseManager

    DB_AVAILABLE = True
except ImportError:
    print("⚠️ Sistema de banco não encontrado.")
    DB_AVAILABLE = False


class ChatDatabaseInterface:
    """Interface MELHORADA para o banco de dados do chat"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'backend', 'banco', 'whatsapp_webhook_realtime.db')

        self.db_path = db_path
        self.db_manager = None
        self._contacts_cache = {}  # Cache de nomes dos contatos
        self._last_message_count = 0  # Para detectar novas mensagens
        self._chat_cache = {}

        if DB_AVAILABLE:
            try:
                self.db_manager = WhatsAppDatabaseManager(db_path)
                print(f"✅ Conectado ao banco: {db_path}")
                self._build_contacts_cache()
            except Exception as e:
                print(f"❌ Erro ao conectar ao banco: {e}")
                self.db_manager = None
        else:
            print("❌ Database manager não disponível")

    def _build_contacts_cache(self):
        """Constrói cache de nomes dos contatos da tabela senders"""
        if not self.is_connected():
            return

        try:
            print("🔍 Construindo cache de nomes dos contatos...")

            with self.db_manager.get_session() as session:
                from backend.banco.models_updated import Sender

                # Buscar todos os senders únicos
                senders = session.query(Sender.sender_id, Sender.push_name, Sender.verified_biz_name) \
                    .filter(Sender.push_name.isnot(None)) \
                    .filter(Sender.push_name != '') \
                    .distinct(Sender.sender_id) \
                    .all()

                for sender_id, push_name, biz_name in senders:
                    if sender_id and push_name:
                        # Usar nome do negócio se disponível, senão push_name
                        display_name = biz_name if biz_name else push_name
                        self._contacts_cache[sender_id] = display_name

            print(f"✅ Cache construído: {len(self._contacts_cache)} contatos")

        except Exception as e:
            print(f"⚠️ Erro ao construir cache: {e}")

    def get_contact_name(self, contact_id: str) -> str:
        """Obtém nome do contato do cache ou formata número"""
        if not contact_id:
            return "Desconhecido"

        # Verificar cache primeiro
        if contact_id in self._contacts_cache:
            return self._contacts_cache[contact_id]

        # Tentar buscar no banco em tempo real
        try:
            with self.db_manager.get_session() as session:
                from backend.banco.models_updated import Sender

                sender = session.query(Sender.push_name, Sender.verified_biz_name) \
                    .filter(Sender.sender_id == contact_id) \
                    .filter(Sender.push_name.isnot(None)) \
                    .first()

                if sender:
                    name = sender.verified_biz_name if sender.verified_biz_name else sender.push_name
                    self._contacts_cache[contact_id] = name  # Atualizar cache
                    return name

        except Exception as e:
            print(f"⚠️ Erro ao buscar nome: {e}")

        # Fallback: formatar número
        return self._format_phone(contact_id)

    def is_connected(self) -> bool:
        """Verifica se está conectado ao banco"""
        return self.db_manager is not None

    def check_for_new_messages(self) -> bool:
        """Verifica se há novas mensagens no banco"""
        if not self.is_connected():
            return False

        try:
            db_info = self.db_manager.get_database_info()
            current_count = db_info.get('total_events', 0)

            if current_count > self._last_message_count:
                self._last_message_count = current_count
                print(f"🔔 Nova mensagem detectada! Total: {current_count}")
                return True

            return False

        except Exception as e:
            print(f"⚠️ Erro ao verificar novas mensagens: {e}")
            return False

    def get_chats_list(self, limit: int = 50, progress_callback=None) -> List[Dict]:
        """
        VERSÃO MELHORADA: Lista de chats com nomes corretos e progresso
        """
        if not self.is_connected():
            return []

        try:
            if progress_callback:
                progress_callback("Conectando ao banco...")

            # Buscar mensagens recentes
            recent_messages = self.db_manager.get_recent_messages(2000)

            if not recent_messages:
                if progress_callback:
                    progress_callback("Nenhuma mensagem encontrada")
                return []

            if progress_callback:
                progress_callback(f"Processando {len(recent_messages)} mensagens...")

            unique_chats = {}
            processed_count = 0

            for idx, msg in enumerate(recent_messages):
                try:
                    # Atualizar progresso a cada 100 mensagens
                    if progress_callback and idx % 100 == 0:
                        progress = int((idx / len(recent_messages)) * 100)
                        progress_callback(f"Processando... {progress}%")

                    is_group = msg.get('isGroup', False)
                    from_me = msg.get('fromMe', False)

                    # Determinar chat_id e nome MELHORADO
                    if is_group:
                        chat_id = msg.get('chat', {}).get('id', '')
                        chat_name = self._extract_group_name(msg)
                        chat_type = 'group'
                    else:
                        if from_me:
                            chat_id = msg.get('chat', {}).get('id', '')
                        else:
                            chat_id = msg.get('sender', {}).get('id', '')

                        # MELHORIA: Usar nome do cache
                        chat_name = self.get_contact_name(chat_id)
                        chat_type = 'individual'

                    if not chat_id:
                        continue

                    # Timestamp da mensagem
                    moment = msg.get('moment', 0)
                    if not moment:
                        try:
                            created_at = msg.get('_db_info', {}).get('saved_at', '')
                            if created_at:
                                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                moment = int(dt.timestamp())
                        except:
                            moment = int(datetime.now().timestamp())

                    # Só atualizar se esta mensagem for mais recente
                    if chat_id not in unique_chats or moment > unique_chats[chat_id]['last_message_time']:
                        unique_chats[chat_id] = {
                            'chat_id': chat_id,
                            'chat_name': chat_name,
                            'chat_type': chat_type,
                            'last_message_time': moment,
                            'last_message': self._extract_message_content(msg),
                            'last_message_from_me': from_me,
                            'message_count': 0,
                            'is_group': is_group,
                            'unread_count': 0,
                            'profile_picture': msg.get('sender', {}).get('profilePicture', '') if not from_me else '',
                            'participants_count': 1 if chat_type == 'individual' else 0,
                            'is_business': bool(msg.get('sender', {}).get('verifiedBizName', '')),
                            'business_name': msg.get('sender', {}).get('verifiedBizName', '')
                        }
                        processed_count += 1

                except Exception as e:
                    continue

            if progress_callback:
                progress_callback(f"Contando mensagens para {len(unique_chats)} chats...")

            # Contar mensagens para cada chat
            for chat_id, chat_data in unique_chats.items():
                count = 0
                for msg in recent_messages:
                    if self._message_belongs_to_chat(msg, chat_id, chat_data['chat_type'] == 'group'):
                        count += 1

                chat_data['message_count'] = count
                chat_data['total_messages'] = count

                if chat_data['chat_type'] == 'group':
                    chat_data['participants_count'] = self._estimate_group_participants(chat_id, recent_messages)

            # Ordenar por mensagem mais recente
            chats_list = list(unique_chats.values())
            chats_list.sort(key=lambda x: x['last_message_time'], reverse=True)

            if progress_callback:
                progress_callback(f"✅ {len(chats_list)} conversas carregadas")

            print(f"✅ {len(chats_list)} chats únicos processados com nomes corretos")
            return chats_list[:limit]

        except Exception as e:
            print(f"❌ Erro ao buscar chats: {e}")
            if progress_callback:
                progress_callback(f"Erro: {str(e)}")
            return []

    def get_chat_messages(self, chat_id: str, limit: int = 100, progress_callback=None) -> List[Dict]:
        """
        VERSÃO MELHORADA: Mensagens com nomes corretos e progresso
        """
        if not self.is_connected():
            return []

        try:
            if progress_callback:
                progress_callback("Carregando mensagens...")

            # Buscar mensagens
            all_messages = self.db_manager.get_recent_messages(3000)

            if not all_messages:
                if progress_callback:
                    progress_callback("Nenhuma mensagem encontrada")
                return []

            if progress_callback:
                progress_callback("Filtrando mensagens do chat...")

            # Determinar se é grupo
            is_group = False
            for msg in all_messages[:100]:
                if msg.get('chat', {}).get('id', '') == chat_id and msg.get('isGroup', False):
                    is_group = True
                    break

            # Filtrar mensagens do chat
            chat_messages = []
            filtered_count = 0

            for idx, msg in enumerate(all_messages):
                if progress_callback and idx % 200 == 0:
                    progress = int((idx / len(all_messages)) * 50)
                    progress_callback(f"Filtrando... {progress}%")

                if self._message_belongs_to_chat(msg, chat_id, is_group):
                    processed_msg = self._process_message_for_chat(msg)
                    if processed_msg:
                        chat_messages.append(processed_msg)
                        filtered_count += 1

            if progress_callback:
                progress_callback("Ordenando cronologicamente...")

            # Ordenar cronologicamente (antigas -> recentes)
            chat_messages.sort(key=lambda x: (x['timestamp'], x.get('message_id', '')))

            # Remover duplicatas
            seen_ids = set()
            unique_messages = []
            for msg in chat_messages:
                msg_id = msg.get('message_id', '')
                if msg_id and msg_id not in seen_ids:
                    seen_ids.add(msg_id)
                    unique_messages.append(msg)
                elif not msg_id:
                    unique_messages.append(msg)

            if progress_callback:
                progress_callback(f"✅ {len(unique_messages)} mensagens carregadas")

            # Retornar mensagens limitadas
            if len(unique_messages) <= limit:
                result = unique_messages
            else:
                result = unique_messages[-limit:]

            print(f"✅ {len(result)} mensagens carregadas com nomes corretos")
            return result

        except Exception as e:
            print(f"❌ Erro ao buscar mensagens: {e}")
            if progress_callback:
                progress_callback(f"Erro: {str(e)}")
            return []

    def _message_belongs_to_chat(self, msg: Dict, chat_id: str, is_group: bool) -> bool:
        """Verifica se mensagem pertence ao chat"""
        try:
            if is_group:
                return msg.get('chat', {}).get('id', '') == chat_id
            else:
                msg_sender_id = msg.get('sender', {}).get('id', '')
                msg_chat_id = msg.get('chat', {}).get('id', '')
                return msg_sender_id == chat_id or msg_chat_id == chat_id
        except Exception:
            return False

    def _process_message_for_chat(self, msg: Dict) -> Optional[Dict]:
        """Processa mensagem com nomes corretos dos contatos"""
        try:
            message_id = msg.get('messageId', '')
            is_group = msg.get('isGroup', False)
            from_me = msg.get('fromMe', False)

            # Timestamp
            timestamp = msg.get('moment', 0)
            if not timestamp:
                try:
                    created_at = msg.get('_db_info', {}).get('saved_at', '')
                    if created_at:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        timestamp = int(dt.timestamp())
                    else:
                        timestamp = int(datetime.now().timestamp())
                except:
                    timestamp = int(datetime.now().timestamp())

            # MELHORIA: Nome do remetente usando cache
            if from_me:
                sender_name = "Você"
                sender_id = ""
            else:
                sender_id = msg.get('sender', {}).get('id', '')
                sender_name = self.get_contact_name(sender_id)

            # Converter timestamp para strings
            try:
                dt = datetime.fromtimestamp(timestamp)
                timestamp_str = dt.strftime('%H:%M')
                date_str = dt.strftime('%d/%m/%Y')
            except Exception:
                timestamp_str = 'N/A'
                date_str = 'N/A'

            # Extrair conteúdo e tipo
            content = self._extract_message_content(msg)
            message_type = self._detect_message_type(msg)

            # Dados de mídia
            media_data = None
            if message_type != 'text':
                media_data = self._extract_media_data(msg, message_type)

            return {
                'message_id': message_id,
                'sender_name': sender_name,
                'content': content,
                'timestamp': timestamp,
                'timestamp_str': timestamp_str,
                'date_str': date_str,
                'from_me': from_me,
                'is_group': is_group,
                'message_type': message_type,
                'media_data': media_data,
                'sender_id': sender_id
            }

        except Exception as e:
            print(f"⚠️ Erro ao processar mensagem: {e}")
            return None

    def _extract_group_name(self, msg: Dict) -> str:
        """Extrai nome do grupo"""
        group_name = (
                msg.get('chat', {}).get('name', '') or
                msg.get('chat', {}).get('groupName', '') or
                msg.get('groupName', '') or
                'Grupo Sem Nome'
        )
        return group_name

    def _estimate_group_participants(self, group_id: str, messages: List[Dict]) -> int:
        """Estima número de participantes do grupo"""
        participants = set()
        for msg in messages:
            if msg.get('chat', {}).get('id') == group_id and msg.get('isGroup', False):
                sender_id = msg.get('sender', {}).get('id', '')
                if sender_id:
                    participants.add(sender_id)
        return max(len(participants), 1)

    def _extract_message_content(self, msg: Dict) -> str:
        """Extrai conteúdo da mensagem"""
        msg_content = msg.get('msgContent', {})

        if 'conversation' in msg_content:
            return msg_content['conversation']
        elif 'stickerMessage' in msg_content:
            return '🏷️ Sticker'
        elif 'imageMessage' in msg_content:
            caption = msg_content['imageMessage'].get('caption', '')
            return f'📷 Imagem{": " + caption if caption else ""}'
        elif 'videoMessage' in msg_content:
            caption = msg_content['videoMessage'].get('caption', '')
            return f'🎥 Vídeo{": " + caption if caption else ""}'
        elif 'audioMessage' in msg_content:
            return '🎵 Mensagem de áudio'
        elif 'documentMessage' in msg_content:
            filename = msg_content['documentMessage'].get('fileName', 'documento')
            return f'📄 {filename}'
        elif 'locationMessage' in msg_content:
            location_name = msg_content['locationMessage'].get('name', 'Localização')
            return f'📍 {location_name}'
        elif 'pollCreationMessageV3' in msg_content:
            poll_name = msg_content['pollCreationMessageV3'].get('name', 'Enquete')
            return f'📊 {poll_name}'
        else:
            return '📱 Mensagem multimídia'

    def _detect_message_type(self, msg: Dict) -> str:
        """Detecta tipo da mensagem"""
        msg_content = msg.get('msgContent', {})

        if 'conversation' in msg_content:
            return 'text'
        elif 'stickerMessage' in msg_content:
            return 'sticker'
        elif 'imageMessage' in msg_content:
            return 'image'
        elif 'videoMessage' in msg_content:
            return 'video'
        elif 'audioMessage' in msg_content:
            return 'audio'
        elif 'documentMessage' in msg_content:
            return 'document'
        elif 'locationMessage' in msg_content:
            return 'location'
        elif 'pollCreationMessageV3' in msg_content:
            return 'poll'
        else:
            return 'unknown'

    def _extract_media_data(self, msg: Dict, message_type: str) -> Dict:
        """Extrai dados específicos de mídia"""
        msg_content = msg.get('msgContent', {})
        media_data = {}

        try:
            if message_type == 'image' and 'imageMessage' in msg_content:
                image = msg_content['imageMessage']
                media_data = {
                    'url': image.get('url', ''),
                    'caption': image.get('caption', ''),
                    'mimetype': image.get('mimetype', ''),
                    'width': image.get('width'),
                    'height': image.get('height')
                }
            elif message_type == 'document' and 'documentMessage' in msg_content:
                doc = msg_content['documentMessage']
                media_data = {
                    'filename': doc.get('fileName', ''),
                    'mimetype': doc.get('mimetype', ''),
                    'file_length': doc.get('fileLength', 0)
                }
            elif message_type == 'location' and 'locationMessage' in msg_content:
                location = msg_content['locationMessage']
                media_data = {
                    'latitude': location.get('degreesLatitude'),
                    'longitude': location.get('degreesLongitude'),
                    'name': location.get('name', ''),
                    'address': location.get('address', '')
                }
            elif message_type == 'poll' and 'pollCreationMessageV3' in msg_content:
                poll = msg_content['pollCreationMessageV3']
                options = [opt.get('optionName', '') for opt in poll.get('options', [])]
                media_data = {
                    'name': poll.get('name', ''),
                    'options': options,
                    'selectable_count': poll.get('selectableOptionsCount', 1)
                }
        except Exception as e:
            print(f"⚠️ Erro ao extrair dados de mídia: {e}")

        return media_data

    def _format_phone(self, phone: str) -> str:
        """Formata número de telefone"""
        if not phone:
            return "Número Desconhecido"

        # Extrair apenas números
        numbers = ''.join(filter(str.isdigit, phone))

        if len(numbers) == 11:  # Celular brasileiro
            return f"({numbers[:2]}) {numbers[2:7]}-{numbers[7:]}"
        elif len(numbers) == 10:  # Fixo brasileiro
            return f"({numbers[:2]}) {numbers[2:6]}-{numbers[6:]}"
        elif len(numbers) >= 12 and numbers.startswith('55'):
            # Com código do país
            num_br = numbers[2:]
            if len(num_br) == 11:
                return f"({num_br[:2]}) {num_br[2:7]}-{num_br[7:]}"
            elif len(num_br) == 10:
                return f"({num_br[:2]}) {num_br[2:6]}-{num_br[6:]}"

        return phone

    def get_database_stats(self) -> Dict:
        """Retorna estatísticas do banco"""
        if not self.is_connected():
            return {}

        try:
            return self.db_manager.get_database_info()
        except Exception as e:
            print(f"❌ Erro ao obter stats: {e}")
            return {}

    def refresh_contacts_cache(self):
        """Atualiza cache de nomes dos contatos"""
        print("🔄 Atualizando cache de contatos...")
        self._build_contacts_cache()

    # Compatibilidade com interface antiga
    def get_contacts_list(self, limit: int = 50, progress_callback=None) -> List[Dict]:
        """Wrapper para compatibilidade"""
        chats = self.get_chats_list(limit, progress_callback)

        contacts = []
        for chat in chats:
            contacts.append({
                'contact_id': chat['chat_id'],
                'contact_name': chat['chat_name'],
                'last_message': chat['last_message'],
                'last_message_time': chat['last_message_time'],
                'last_message_from_me': chat['last_message_from_me'],
                'total_messages': chat['total_messages'],
                'is_group': chat['chat_type'] == 'group',
                'profile_picture': chat['profile_picture'],
                'is_business': chat['is_business'],
                'business_name': chat['business_name']
            })

        return contacts