#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface OTIMIZADA para o banco de dados WhatsApp - SEM RECARREGAMENTO TOTAL
CORREÇÃO: Carregamento incremental para evitar reinicialização da interface
"""
import sqlite3
import sys
import os
from contextlib import contextmanager
from typing import List, Dict, Optional, Set
from datetime import datetime, date
from collections import defaultdict

# Adicionar caminho do backend
backend_path = os.path.join(os.path.dirname(__file__), 'backend', 'banco')
sys.path.insert(0, backend_path)

try:
    from database_manager_updated import WhatsAppDatabaseManager

    DB_AVAILABLE = True
except ImportError:
    print("⚠️ Sistema de banco não encontrado. Verifique se os arquivos estão no caminho correto.")
    DB_AVAILABLE = False




class ChatDatabaseInterface:
    """Interface OTIMIZADA com carregamento incremental - SEM RECARREGAMENTO TOTAL"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'backend', 'banco', 'whatsapp_webhook_realtime.db')

        self.db_path = db_path
        self.db_manager = None
        self._contacts_cache = {}  # Cache de nomes dos contatos
        self._loaded_messages_cache = {}  # Cache de mensagens já carregadas por chat
        self._last_message_timestamps = {}  # Último timestamp por chat
        self._last_message_count = 0

        if DB_AVAILABLE:
            try:
                self.db_manager = WhatsAppDatabaseManager(db_path)
                print(f"✅ Conectado ao banco otimizado: {db_path}")
                self._build_contacts_cache()
            except Exception as e:
                print(f"❌ Erro ao conectar ao banco: {e}")
                self.db_manager = None
        else:
            print("❌ Database manager não disponível")

    @contextmanager
    def get_session(self):
        """Context manager para sessões SQLite - ADICIONE ESTE MÉTODO"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
            yield conn
        except Exception as e:
            print(f"❌ Erro na sessão do banco: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def get_chat_messages_initial(self, contact_id: str, limit: int = 30) -> List[Dict]:
        """Carrega mensagens iniciais do chat - VERSÃO CORRIGIDA"""
        try:
            print(f"🔍 Buscando mensagens para contato: {contact_id}")

            with self.get_session() as conn:
                # Query simples para buscar mensagens
                query = """
                SELECT 
                    w.message_id,
                    w.from_me,
                    w.is_group,
                    w.moment,
                    w.created_at,
                    s.sender_id,
                    s.push_name as sender_name,
                    mc.message_type,
                    mc.text_content,
                    mc.media_caption,
                    mc.document_filename
                FROM webhook_events w
                LEFT JOIN senders s ON w.id = s.event_id
                LEFT JOIN message_contents mc ON w.id = mc.event_id
                WHERE (s.sender_id = ? OR w.connected_phone = ?)
                AND w.message_id IS NOT NULL 
                AND w.message_id != ''
                ORDER BY w.created_at DESC
                LIMIT ?
                """

                cursor = conn.execute(query, (contact_id, contact_id, limit))
                messages = []

                for row in cursor.fetchall():
                    # Extrair conteúdo
                    if row['message_type'] == 'text':
                        content = row['text_content'] or ''
                    elif row['message_type'] == 'image':
                        content = f"📷 Imagem: {row['media_caption'] or ''}"
                    elif row['message_type'] == 'document':
                        content = f"📄 {row['document_filename'] or 'Documento'}"
                    else:
                        content = row['text_content'] or '📱 Mensagem'

                    # Timestamp
                    if row['moment']:
                        timestamp = int(row['moment'])
                    else:
                        from datetime import datetime
                        created_at = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
                        timestamp = int(created_at.timestamp())

                    message_data = {
                        'message_id': row['message_id'],  # ✅ ID real do banco
                        'sender_name': row['sender_name'] or 'Desconhecido',
                        'content': content,
                        'timestamp': timestamp,
                        'timestamp_str': datetime.fromtimestamp(timestamp).strftime('%H:%M'),
                        'date_str': datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y'),
                        'from_me': bool(row['from_me']),
                        'is_group': bool(row['is_group']),
                        'message_type': row['message_type'] or 'text',
                        'media_data': None,
                        'sender_id': row['sender_id'] or '',
                        'contact_id': contact_id
                    }
                    messages.append(message_data)

                messages_ordered = list(reversed(messages))
                print(f"💬 Carregadas {len(messages_ordered)} mensagens")
                return messages_ordered

        except Exception as e:
            print(f"❌ Erro ao carregar mensagens: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_new_messages_incremental(self, contact_id: str) -> List[Dict]:
        """Busca novas mensagens incrementalmente - VERSÃO CORRIGIDA"""
        try:
            last_check = self.cache_timestamps.get(contact_id, 0)
            current_time = int(datetime.now().timestamp())

            with self.get_session() as conn:
                query = """
                SELECT 
                    w.message_id,
                    w.from_me,
                    w.moment,
                    w.created_at,
                    s.push_name as sender_name,
                    mc.message_type,
                    mc.text_content
                FROM webhook_events w
                LEFT JOIN senders s ON w.id = s.event_id
                LEFT JOIN message_contents mc ON w.id = mc.event_id
                WHERE (s.sender_id = ? OR w.connected_phone = ?)
                AND w.created_at > datetime(?, 'unixepoch')
                AND w.message_id IS NOT NULL
                ORDER BY w.created_at ASC
                LIMIT 10
                """

                cursor = conn.execute(query, (contact_id, contact_id, last_check))
                new_messages = []

                for row in cursor.fetchall():
                    content = row['text_content'] or '📱 Mensagem'

                    if row['moment']:
                        timestamp = int(row['moment'])
                    else:
                        created_at = datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))
                        timestamp = int(created_at.timestamp())

                    message_data = {
                        'message_id': row['message_id'],
                        'sender_name': row['sender_name'] or 'Desconhecido',
                        'content': content,
                        'timestamp': timestamp,
                        'timestamp_str': datetime.fromtimestamp(timestamp).strftime('%H:%M'),
                        'date_str': datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y'),
                        'from_me': bool(row['from_me']),
                        'is_group': False,
                        'message_type': row['message_type'] or 'text',
                        'media_data': None,
                        'sender_id': '',
                        'contact_id': contact_id
                    }
                    new_messages.append(message_data)

                self.cache_timestamps[contact_id] = current_time
                return new_messages

        except Exception as e:
            print(f"❌ Erro ao buscar novas mensagens: {e}")
            return []

    def _build_contacts_cache(self):
        """Constrói cache de nomes dos contatos"""
        if not self.is_connected():
            return

        try:
            print("🔍 Construindo cache de nomes...")

            with self.db_manager.get_session() as session:
                from backend.banco.models_updated import Sender

                senders = session.query(Sender.sender_id, Sender.push_name, Sender.verified_biz_name) \
                    .filter(Sender.push_name.isnot(None)) \
                    .filter(Sender.push_name != '') \
                    .distinct(Sender.sender_id) \
                    .all()

                for sender_id, push_name, biz_name in senders:
                    if sender_id and push_name:
                        display_name = biz_name if biz_name else push_name
                        self._contacts_cache[sender_id] = display_name

            print(f"✅ Cache construído: {len(self._contacts_cache)} contatos")

        except Exception as e:
            print(f"⚠️ Erro ao construir cache: {e}")

    def get_contact_name(self, contact_id: str) -> str:
        """Obtém nome do contato do cache"""
        if not contact_id:
            return "Desconhecido"

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
                    self._contacts_cache[contact_id] = name
                    return name

        except Exception as e:
            print(f"⚠️ Erro ao buscar nome: {e}")

        return self._format_phone(contact_id)

    def is_connected(self) -> bool:
        """Verifica se está conectado ao banco"""
        return self.db_manager is not None

    def get_chats_list(self, limit: int = 50) -> List[Dict]:
        """Retorna lista de chats otimizada"""
        if not self.is_connected():
            return []

        try:
            print("🔍 Buscando chats únicos otimizado...")

            recent_messages = self.db_manager.get_recent_messages(2000)

            if not recent_messages:
                print("📭 Nenhuma mensagem encontrada")
                return []

            unique_chats = {}

            for idx, msg in enumerate(recent_messages):
                try:
                    is_group = msg.get('isGroup', False)
                    from_me = msg.get('fromMe', False)

                    if is_group:
                        chat_id = msg.get('chat', {}).get('id', '')
                        chat_name = self._extract_group_name(msg)
                        chat_type = 'group'
                    else:
                        if from_me:
                            chat_id = msg.get('chat', {}).get('id', '')
                            chat_name = self.get_contact_name(chat_id)
                        else:
                            chat_id = msg.get('sender', {}).get('id', '')
                            chat_name = msg.get('sender', {}).get('pushName', '') or self.get_contact_name(chat_id)

                        chat_type = 'individual'

                    if not chat_id:
                        continue

                    moment = msg.get('moment', 0)
                    if not moment:
                        try:
                            created_at = msg.get('_db_info', {}).get('saved_at', '')
                            if created_at:
                                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                moment = int(dt.timestamp())
                        except:
                            moment = int(datetime.now().timestamp())

                    if chat_id not in unique_chats or moment > unique_chats[chat_id]['last_message_time']:
                        unique_chats[chat_id] = {
                            'chat_id': chat_id,
                            'chat_name': chat_name or self._format_phone(chat_id),
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

                except Exception as e:
                    continue

            # Contar mensagens
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

            print(f"✅ {len(chats_list)} chats processados")
            return chats_list[:limit]

        except Exception as e:
            print(f"❌ Erro ao buscar chats: {e}")
            return []

    def get_chat_messages_initial(self, chat_id: str, limit: int = 30) -> List[Dict]:
        """
        NOVO: Carrega mensagens iniciais do chat (primeira vez)
        Retorna apenas mensagens mais recentes para carregamento inicial
        """
        if not self.is_connected():
            return []

        try:
            print(f"📨 Carregamento INICIAL: {limit} mensagens do chat: {chat_id[:15]}")

            all_messages = self.db_manager.get_recent_messages(3000)
            if not all_messages:
                return []

            # Determinar se é grupo
            is_group = self._detect_if_group(chat_id, all_messages)

            # Filtrar e processar mensagens do chat
            chat_messages = self._filter_and_process_messages(chat_id, all_messages, is_group)

            # Ordenar cronologicamente
            chat_messages.sort(key=lambda x: (x['timestamp'], x.get('message_id', '')))

            # Remover duplicatas
            unique_messages = self._remove_duplicates(chat_messages)

            # Cache inicial - apenas IDs das mensagens carregadas
            self._loaded_messages_cache[chat_id] = {
                msg.get('message_id', f"temp_{msg['timestamp']}"): msg
                for msg in unique_messages
            }

            # Armazenar último timestamp
            if unique_messages:
                self._last_message_timestamps[chat_id] = max(msg['timestamp'] for msg in unique_messages)

            # Retornar apenas as mais recentes até o limite
            if len(unique_messages) <= limit:
                result = unique_messages
            else:
                result = unique_messages[-limit:]

            print(f"✅ Carregamento inicial: {len(result)} mensagens")
            return result

        except Exception as e:
            print(f"❌ Erro no carregamento inicial: {e}")
            return []

    def get_new_messages_incremental(self, chat_id: str) -> List[Dict]:
        """
        NOVO: Busca apenas NOVAS mensagens desde o último carregamento
        Retorna lista vazia se não há novas mensagens
        """
        if not self.is_connected():
            return []

        try:
            # Verificar se temos cache para este chat
            if chat_id not in self._loaded_messages_cache:
                print(f"⚠️ Cache não encontrado para {chat_id}, fazendo carregamento inicial")
                return self.get_chat_messages_initial(chat_id)

            last_timestamp = self._last_message_timestamps.get(chat_id, 0)

            print(f"🔍 Verificando novas mensagens para {chat_id[:15]} após {last_timestamp}")

            # Buscar mensagens recentes
            all_messages = self.db_manager.get_recent_messages(1000)
            if not all_messages:
                return []

            # Determinar se é grupo
            is_group = self._detect_if_group(chat_id, all_messages)

            # Filtrar mensagens do chat que são NOVAS (timestamp > último conhecido)
            new_messages = []
            known_message_ids = set(self._loaded_messages_cache[chat_id].keys())

            for msg in all_messages:
                if not self._message_belongs_to_chat(msg, chat_id, is_group):
                    continue

                processed_msg = self._process_message_for_chat(msg)
                if not processed_msg or processed_msg['timestamp'] <= last_timestamp:
                    continue

                msg_id = processed_msg.get('message_id', f"temp_{processed_msg['timestamp']}")

                # Verificar se é realmente uma mensagem nova
                if msg_id not in known_message_ids:
                    new_messages.append(processed_msg)

            if not new_messages:
                return []

            # Ordenar novas mensagens
            new_messages.sort(key=lambda x: (x['timestamp'], x.get('message_id', '')))

            # Atualizar cache com novas mensagens
            for msg in new_messages:
                msg_id = msg.get('message_id', f"temp_{msg['timestamp']}")
                self._loaded_messages_cache[chat_id][msg_id] = msg

            # Atualizar timestamp
            if new_messages:
                self._last_message_timestamps[chat_id] = max(msg['timestamp'] for msg in new_messages)

            print(f"✅ {len(new_messages)} NOVAS mensagens encontradas")
            return new_messages

        except Exception as e:
            print(f"❌ Erro na busca incremental: {e}")
            return []

    def get_messages_before_pagination(self, chat_id: str, before_timestamp: float, limit: int = 20) -> List[Dict]:
        """
        NOVO: Carrega mensagens antigas para paginação (scroll para cima)
        """
        if not self.is_connected():
            return []

        try:
            print(f"📜 Paginação: {limit} mensagens antes de {before_timestamp}")

            # Usar cache se disponível, senão buscar do banco
            if chat_id in self._loaded_messages_cache:
                all_chat_messages = list(self._loaded_messages_cache[chat_id].values())
            else:
                # Buscar do banco se cache não disponível
                all_messages = self.db_manager.get_recent_messages(5000)
                is_group = self._detect_if_group(chat_id, all_messages)
                all_chat_messages = self._filter_and_process_messages(chat_id, all_messages, is_group)

            # Filtrar mensagens antes do timestamp
            older_messages = [
                msg for msg in all_chat_messages
                if msg['timestamp'] < before_timestamp
            ]

            # Ordenar e pegar as mais recentes das antigas
            older_messages.sort(key=lambda x: (x['timestamp'], x.get('message_id', '')))

            if len(older_messages) <= limit:
                result = older_messages
            else:
                result = older_messages[-limit:]

            print(f"✅ Paginação: {len(result)} mensagens antigas")
            return result

        except Exception as e:
            print(f"❌ Erro na paginação: {e}")
            return []

    def _detect_if_group(self, chat_id: str, messages: List[Dict]) -> bool:
        """Detecta se o chat é um grupo"""
        for msg in messages[:100]:  # Verificar primeiras 100 mensagens
            if msg.get('chat', {}).get('id', '') == chat_id and msg.get('isGroup', False):
                return True
        return False

    def _filter_and_process_messages(self, chat_id: str, all_messages: List[Dict], is_group: bool) -> List[Dict]:
        """Filtra e processa mensagens de um chat específico"""
        chat_messages = []

        for msg in all_messages:
            if self._message_belongs_to_chat(msg, chat_id, is_group):
                processed_msg = self._process_message_for_chat(msg)
                if processed_msg and processed_msg['timestamp'] > 0:
                    chat_messages.append(processed_msg)

        return chat_messages

    def _remove_duplicates(self, messages: List[Dict]) -> List[Dict]:
        """Remove mensagens duplicadas baseado no message_id"""
        seen_ids = set()
        unique_messages = []

        for msg in messages:
            msg_id = msg.get('message_id', '')
            if msg_id and msg_id not in seen_ids:
                seen_ids.add(msg_id)
                unique_messages.append(msg)
            elif not msg_id:
                # Mensagens sem ID são adicionadas (podem ser temporárias)
                unique_messages.append(msg)

        return unique_messages

    def process_single_new_message(self, message_data: Dict) -> Optional[Dict]:
        """
        NOVO: Processa uma única mensagem nova (para WebSocket/tempo real)
        Adiciona automaticamente ao cache se for de um chat monitorado
        """
        try:
            print(f"📨 Processando mensagem única: {message_data.get('messageId', 'N/A')}")

            # Processar mensagem
            processed_msg = self._process_message_for_chat(message_data)
            if not processed_msg:
                return None

            # Identificar chat
            chat_id = self._extract_chat_id_from_message(message_data)
            if not chat_id:
                return None

            # Se temos cache para este chat, adicionar mensagem
            if chat_id in self._loaded_messages_cache:
                msg_id = processed_msg.get('message_id', f"temp_{processed_msg['timestamp']}")

                # Verificar se não é duplicata
                if msg_id not in self._loaded_messages_cache[chat_id]:
                    # Adicionar ao cache
                    self._loaded_messages_cache[chat_id][msg_id] = processed_msg

                    # Atualizar timestamp
                    current_max = self._last_message_timestamps.get(chat_id, 0)
                    if processed_msg['timestamp'] > current_max:
                        self._last_message_timestamps[chat_id] = processed_msg['timestamp']

            print(f"✅ Mensagem única processada: {processed_msg.get('content', '')[:50]}")
            return processed_msg

        except Exception as e:
            print(f"⚠️ Erro ao processar mensagem única: {e}")
            return None

    def clear_chat_cache(self, chat_id: str = None):
        """Limpa cache de mensagens (específico ou geral)"""
        if chat_id:
            if chat_id in self._loaded_messages_cache:
                del self._loaded_messages_cache[chat_id]
                del self._last_message_timestamps[chat_id]
                print(f"🗑️ Cache limpo para: {chat_id}")
        else:
            self._loaded_messages_cache.clear()
            self._last_message_timestamps.clear()
            print("🗑️ Cache de mensagens totalmente limpo")

    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        return {
            'chats_cached': len(self._loaded_messages_cache),
            'total_messages_cached': sum(len(cache) for cache in self._loaded_messages_cache.values()),
            'contacts_cached': len(self._contacts_cache)
        }

    # ========== MÉTODOS AUXILIARES (sem mudanças) ==========

    def _extract_chat_id_from_message(self, msg: Dict) -> str:
        """Extrai chat_id de uma mensagem"""
        try:
            is_group = msg.get('isGroup', False)
            from_me = msg.get('fromMe', False)

            if is_group:
                return msg.get('chat', {}).get('id', '')
            else:
                if from_me:
                    return msg.get('chat', {}).get('id', '')
                else:
                    return msg.get('sender', {}).get('id', '')
        except:
            return ''

    def check_for_new_messages(self) -> bool:
        """Verifica se há novas mensagens (backup check)"""
        if not self.is_connected():
            return False

        try:
            db_info = self.db_manager.get_database_info()
            current_count = db_info.get('total_events', 0)

            if current_count > self._last_message_count:
                self._last_message_count = current_count
                print(f"🔔 Novas mensagens detectadas! Total: {current_count}")
                return True

            return False

        except Exception as e:
            print(f"⚠️ Erro ao verificar novas mensagens: {e}")
            return False

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
        """Processa mensagem com timestamps corretos"""
        try:
            message_id = msg.get('messageId', '')
            is_group = msg.get('isGroup', False)
            from_me = msg.get('fromMe', False)

            # Timestamp mais confiável
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

            # Nome do remetente
            if from_me:
                sender_name = "Você"
                sender_id = ""
            else:
                sender_id = msg.get('sender', {}).get('id', '')
                sender_name = msg.get('sender', {}).get('pushName', '')
                if not sender_name:
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
        """Extrai o conteúdo principal da mensagem"""
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
        """Detecta o tipo da mensagem"""
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

        numbers = ''.join(filter(str.isdigit, phone))

        if len(numbers) == 11:  # Celular brasileiro
            return f"({numbers[:2]}) {numbers[2:7]}-{numbers[7:]}"
        elif len(numbers) == 10:  # Fixo brasileiro
            return f"({numbers[:2]}) {numbers[2:6]}-{numbers[6:]}"
        elif len(numbers) >= 12 and numbers.startswith('55'):
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
    def get_contacts_list(self, limit: int = 50) -> List[Dict]:
        """Wrapper para compatibilidade"""
        chats = self.get_chats_list(limit)

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

    # NOVOS MÉTODOS PARA COMPATIBILIDADE
    def get_chat_messages(self, chat_id: str, limit: int = 50) -> List[Dict]:
        """
        Método de compatibilidade - usa carregamento inicial
        Para manter compatibilidade com código existente
        """
        return self.get_chat_messages_initial(chat_id, limit)