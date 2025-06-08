#!/usr/bin/env python3
"""
Gerenciador do banco de dados para webhooks do WhatsApp
Classe principal para todas as operações de banco
"""

import json
import logging
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, desc, and_, or_

from models_updated import (
    WebhookEvent, Chat, Sender, MessageContent, MessageStats, ContactStats,
    init_database, create_database_engine, create_session_factory
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppDatabaseManager:
    """Gerenciador principal do banco de dados"""

    def __init__(self, db_path="whatsapp_webhook.db"):
        """Inicializa o gerenciador do banco"""
        self.db_path = db_path
        self.engine, self.Session = init_database(db_path)
        logger.info(f"✅ Banco de dados inicializado: {db_path}")

    @contextmanager
    def get_session(self):
        """Context manager para sessões do banco"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Erro na sessão do banco: {e}")
            raise
        finally:
            session.close()

    def save_webhook_data(self, webhook_data: Dict) -> bool:
        """
        Salva dados do webhook no banco de dados

        Args:
            webhook_data: Dados completos do webhook

        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            with self.get_session() as session:
                # Verificar se já existe essa mensagem
                existing = session.query(WebhookEvent).filter_by(
                    message_id=webhook_data.get('messageId')
                ).first()

                if existing:
                    logger.warning(f"⚠️  Mensagem já existe: {webhook_data.get('messageId')}")
                    return False

                # Criar evento principal
                event = WebhookEvent(
                    event_type=webhook_data.get('event', 'unknown'),
                    instance_id=webhook_data.get('instanceId', ''),
                    connected_phone=webhook_data.get('connectedPhone', ''),
                    message_id=webhook_data.get('messageId', ''),
                    from_me=webhook_data.get('fromMe', False),
                    from_api=webhook_data.get('fromApi', False),
                    is_group=webhook_data.get('isGroup', False),
                    moment=webhook_data.get('moment', int(datetime.now().timestamp())),
                    raw_json=json.dumps(webhook_data, ensure_ascii=False)
                )

                session.add(event)
                session.flush()  # Para obter o ID

                # Salvar dados do chat
                chat_data = webhook_data.get('chat', {})
                if chat_data:
                    chat = Chat(
                        event_id=event.id,
                        chat_id=chat_data.get('id', ''),
                        profile_picture=chat_data.get('profilePicture', ''),
                        is_group=webhook_data.get('isGroup', False)
                    )
                    session.add(chat)

                # Salvar dados do remetente
                sender_data = webhook_data.get('sender', {})
                if sender_data:
                    sender = Sender(
                        event_id=event.id,
                        sender_id=sender_data.get('id', ''),
                        profile_picture=sender_data.get('profilePicture', ''),
                        push_name=sender_data.get('pushName', ''),
                        verified_biz_name=sender_data.get('verifiedBizName', '')
                    )
                    session.add(sender)

                # Salvar conteúdo da mensagem
                msg_content = webhook_data.get('msgContent', {})
                if msg_content:
                    self._save_message_content(session, event.id, msg_content)

                # Atualizar estatísticas
                self._update_stats(session, webhook_data)

                session.commit()
                logger.info(f"✅ Webhook salvo: {webhook_data.get('messageId')}")
                return True

        except IntegrityError as e:
            logger.warning(f"⚠️  Dados duplicados: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao salvar webhook: {e}")
            return False

    def _save_message_content(self, session, event_id: int, msg_content: Dict):
        """Salva o conteúdo da mensagem baseado no tipo"""

        # Detectar tipo da mensagem
        message_type = "unknown"
        content = MessageContent(
            event_id=event_id,
            raw_content_json=json.dumps(msg_content, ensure_ascii=False)
        )

        # Mensagem de texto
        if 'conversation' in msg_content:
            message_type = "text"
            content.text_content = msg_content['conversation']

        # Mensagem de sticker
        elif 'stickerMessage' in msg_content:
            message_type = "sticker"
            sticker = msg_content['stickerMessage']
            content.sticker_url = sticker.get('url', '')
            content.sticker_mimetype = sticker.get('mimetype', '')
            content.sticker_file_length = sticker.get('fileLength', '')
            content.sticker_is_animated = sticker.get('isAnimated', False)
            content.sticker_is_avatar = sticker.get('isAvatar', False)
            content.sticker_is_ai = sticker.get('isAiSticker', False)
            content.sticker_is_lottie = sticker.get('isLottie', False)
            content.file_sha256 = sticker.get('fileSha256', '')
            content.file_enc_sha256 = sticker.get('fileEncSha256', '')
            content.media_key = sticker.get('mediaKey', '')
            content.direct_path = sticker.get('directPath', '')
            content.media_key_timestamp = sticker.get('mediaKeyTimestamp', '')

        # Mensagem de imagem
        elif 'imageMessage' in msg_content:
            message_type = "image"
            image = msg_content['imageMessage']
            content.media_url = image.get('url', '')
            content.media_mimetype = image.get('mimetype', '')
            content.media_file_length = image.get('fileLength', '')
            content.media_caption = image.get('caption', '')
            content.file_sha256 = image.get('fileSha256', '')
            content.file_enc_sha256 = image.get('fileEncSha256', '')
            content.media_key = image.get('mediaKey', '')
            content.direct_path = image.get('directPath', '')

        # Mensagem de vídeo
        elif 'videoMessage' in msg_content:
            message_type = "video"
            video = msg_content['videoMessage']
            content.media_url = video.get('url', '')
            content.media_mimetype = video.get('mimetype', '')
            content.media_file_length = video.get('fileLength', '')
            content.media_caption = video.get('caption', '')
            content.file_sha256 = video.get('fileSha256', '')
            content.file_enc_sha256 = video.get('fileEncSha256', '')
            content.media_key = video.get('mediaKey', '')
            content.direct_path = video.get('directPath', '')

        # Mensagem de áudio
        elif 'audioMessage' in msg_content:
            message_type = "audio"
            audio = msg_content['audioMessage']
            content.media_url = audio.get('url', '')
            content.media_mimetype = audio.get('mimetype', '')
            content.media_file_length = audio.get('fileLength', '')
            content.file_sha256 = audio.get('fileSha256', '')
            content.file_enc_sha256 = audio.get('fileEncSha256', '')
            content.media_key = audio.get('mediaKey', '')
            content.direct_path = audio.get('directPath', '')

        # Mensagem de documento
        elif 'documentMessage' in msg_content:
            message_type = "document"
            doc = msg_content['documentMessage']
            content.document_url = doc.get('url', '')
            content.document_filename = doc.get('fileName', '')
            content.document_mimetype = doc.get('mimetype', '')
            content.document_file_length = doc.get('fileLength', '')
            content.file_sha256 = doc.get('fileSha256', '')
            content.file_enc_sha256 = doc.get('fileEncSha256', '')
            content.media_key = doc.get('mediaKey', '')
            content.direct_path = doc.get('directPath', '')

        # Mensagem de localização
        elif 'locationMessage' in msg_content:
            message_type = "location"
            location = msg_content['locationMessage']
            content.location_latitude = str(location.get('degreesLatitude', ''))
            content.location_longitude = str(location.get('degreesLongitude', ''))
            content.location_name = location.get('name', '')
            content.location_address = location.get('address', '')

        # Pegar message secret se existir
        context_info = msg_content.get('messageContextInfo', {})
        if context_info:
            content.message_secret = context_info.get('messageSecret', '')

        content.message_type = message_type
        session.add(content)

    def _update_stats(self, session, webhook_data: Dict):
        """Atualiza estatísticas diárias e por contato"""
        today = date.today().strftime('%Y-%m-%d')

        # Estatísticas diárias
        daily_stats = session.query(MessageStats).filter_by(date=today).first()
        if not daily_stats:
            daily_stats = MessageStats(date=today)
            session.add(daily_stats)

        daily_stats.total_messages += 1

        if webhook_data.get('fromMe'):
            daily_stats.messages_sent += 1
        else:
            daily_stats.messages_received += 1

        if webhook_data.get('isGroup'):
            daily_stats.group_messages += 1
        else:
            daily_stats.private_messages += 1

        # Contar por tipo de mensagem
        msg_content = webhook_data.get('msgContent', {})
        if 'stickerMessage' in msg_content:
            daily_stats.sticker_count += 1
        elif 'conversation' in msg_content:
            daily_stats.text_count += 1
        elif any(key in msg_content for key in ['imageMessage', 'videoMessage', 'audioMessage']):
            daily_stats.media_count += 1

        daily_stats.updated_at = datetime.utcnow()

        # Estatísticas por contato
        sender_data = webhook_data.get('sender', {})
        if sender_data and not webhook_data.get('isGroup'):
            contact_id = sender_data.get('id', '')
            if contact_id:
                contact_stats = session.query(ContactStats).filter_by(contact_id=contact_id).first()
                if not contact_stats:
                    contact_stats = ContactStats(
                        contact_id=contact_id,
                        first_message_date=datetime.utcnow()
                    )
                    session.add(contact_stats)

                contact_stats.contact_name = sender_data.get('pushName', '')
                contact_stats.last_profile_picture = sender_data.get('profilePicture', '')
                contact_stats.total_messages += 1
                contact_stats.last_message_date = datetime.utcnow()

                if webhook_data.get('fromMe'):
                    contact_stats.messages_sent_to_them += 1
                else:
                    contact_stats.messages_received_from_them += 1

                if sender_data.get('verifiedBizName'):
                    contact_stats.is_business = True
                    contact_stats.business_name = sender_data.get('verifiedBizName', '')

                contact_stats.updated_at = datetime.utcnow()

    def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        """Retorna mensagens recentes"""
        try:
            with self.get_session() as session:
                events = session.query(WebhookEvent) \
                    .order_by(desc(WebhookEvent.created_at)) \
                    .limit(limit) \
                    .all()

                return [json.loads(event.raw_json) for event in events]
        except Exception as e:
            logger.error(f"❌ Erro ao buscar mensagens: {e}")
            return []

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Retorna estatísticas dos últimos N dias"""
        try:
            with self.get_session() as session:
                stats = session.query(MessageStats) \
                    .order_by(desc(MessageStats.date)) \
                    .limit(days) \
                    .all()

                return [{
                    'date': stat.date,
                    'total_messages': stat.total_messages,
                    'messages_sent': stat.messages_sent,
                    'messages_received': stat.messages_received,
                    'group_messages': stat.group_messages,
                    'private_messages': stat.private_messages,
                    'sticker_count': stat.sticker_count,
                    'text_count': stat.text_count,
                    'media_count': stat.media_count
                } for stat in stats]
        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas: {e}")
            return []

    def get_contact_stats(self, limit: int = 20) -> List[Dict]:
        """Retorna estatísticas dos contatos mais ativos"""
        try:
            with self.get_session() as session:
                contacts = session.query(ContactStats) \
                    .order_by(desc(ContactStats.total_messages)) \
                    .limit(limit) \
                    .all()

                return [{
                    'contact_id': contact.contact_id,
                    'contact_name': contact.contact_name,
                    'total_messages': contact.total_messages,
                    'messages_sent': contact.messages_sent_to_them,
                    'messages_received': contact.messages_received_from_them,
                    'last_message': contact.last_message_date.isoformat() if contact.last_message_date else None,
                    'is_business': contact.is_business,
                    'business_name': contact.business_name
                } for contact in contacts]
        except Exception as e:
            logger.error(f"❌ Erro ao buscar contatos: {e}")
            return []

    def search_messages(self,
                        text: Optional[str] = None,
                        contact_id: Optional[str] = None,
                        message_type: Optional[str] = None,
                        from_me: Optional[bool] = None,
                        is_group: Optional[bool] = None,
                        days_back: int = 30,
                        limit: int = 100) -> List[Dict]:
        """Busca mensagens com filtros avançados"""
        try:
            with self.get_session() as session:
                query = session.query(WebhookEvent)

                # Filtros de data
                if days_back:
                    cutoff_date = datetime.now() - timedelta(days=days_back)
                    query = query.filter(WebhookEvent.created_at >= cutoff_date)

                # Filtros básicos
                if from_me is not None:
                    query = query.filter(WebhookEvent.from_me == from_me)

                if is_group is not None:
                    query = query.filter(WebhookEvent.is_group == is_group)

                # Filtro por contato
                if contact_id:
                    query = query.join(Sender).filter(Sender.sender_id == contact_id)

                # Filtro por tipo de mensagem
                if message_type:
                    query = query.join(MessageContent).filter(MessageContent.message_type == message_type)

                # Filtro por texto
                if text:
                    query = query.join(MessageContent).filter(MessageContent.text_content.contains(text))

                events = query.order_by(desc(WebhookEvent.created_at)).limit(limit).all()
                return [json.loads(event.raw_json) for event in events]

        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return []

    def get_database_info(self) -> Dict:
        """Retorna informações sobre o banco de dados"""
        try:
            with self.get_session() as session:
                total_events = session.query(WebhookEvent).count()
                total_chats = session.query(Chat).count()
                total_senders = session.query(Sender).count()
                total_contents = session.query(MessageContent).count()

                first_message = session.query(WebhookEvent) \
                    .order_by(WebhookEvent.created_at) \
                    .first()

                last_message = session.query(WebhookEvent) \
                    .order_by(desc(WebhookEvent.created_at)) \
                    .first()

                return {
                    'database_path': self.db_path,
                    'total_events': total_events,
                    'total_chats': total_chats,
                    'total_senders': total_senders,
                    'total_message_contents': total_contents,
                    'first_message_date': first_message.created_at.isoformat() if first_message else None,
                    'last_message_date': last_message.created_at.isoformat() if last_message else None,
                    'database_size_mb': round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(
                        self.db_path) else 0
                }
        except Exception as e:
            logger.error(f"❌ Erro ao obter info do banco: {e}")
            return {}