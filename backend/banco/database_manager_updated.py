#!/usr/bin/env python3
"""
Gerenciador atualizado do banco de dados para webhooks do WhatsApp
Sistema otimizado para processamento em tempo real
"""

import json
import logging
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import func, desc, and_, or_, text

# Importar modelos atualizados
from backend.banco.models_updated import (
    WebhookEvent, Chat, Sender, MessageContent, MessageStats, ContactStats, RealTimeStats,
    init_database, create_database_engine, create_session_factory
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppDatabaseManager:
    """Gerenciador principal do banco de dados - VERSÃO ATUALIZADA"""

    def __init__(self, db_path="whatsapp_webhook_realtime.db"):
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
        Salva dados do webhook no banco de dados - VERSÃO OTIMIZADA

        Args:
            webhook_data: Dados completos do webhook

        Returns:
            bool: True se salvou com sucesso, False caso contrário
        """
        try:
            with self.get_session() as session:
                message_id = webhook_data.get('messageId', '')

                # Verificar se já existe essa mensagem
                if message_id:
                    existing = session.query(WebhookEvent).filter_by(message_id=message_id).first()
                    if existing:
                        logger.warning(f"⚠️ Mensagem já existe: {message_id}")
                        return False

                # Criar evento principal
                event = WebhookEvent(
                    event_type=webhook_data.get('event', 'unknown'),
                    instance_id=webhook_data.get('instanceId', ''),
                    connected_phone=webhook_data.get('connectedPhone', ''),
                    message_id=message_id,
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
                self._update_realtime_stats(session, webhook_data)

                session.commit()
                logger.info(f"✅ Webhook salvo: {message_id}")
                return True

        except IntegrityError as e:
            logger.warning(f"⚠️ Dados duplicados: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao salvar webhook: {e}")
            return False

    def _save_message_content(self, session, event_id: int, msg_content: Dict):
        """Salva o conteúdo da mensagem - VERSÃO ATUALIZADA"""

        message_type = "unknown"
        content = MessageContent(
            event_id=event_id,
            raw_content_json=json.dumps(msg_content, ensure_ascii=False)
        )

        # Extrair messageContextInfo se existir
        context_info = msg_content.get('messageContextInfo', {})
        if context_info:
            content.message_secret = context_info.get('messageSecret', '')
            content.device_list_metadata = json.dumps(context_info.get('deviceListMetadata', {}))

        # Mensagem de texto/emoji (conversation)
        if 'conversation' in msg_content:
            message_type = "text"
            content.text_content = msg_content['conversation']

        # Mensagem de sticker
        elif 'stickerMessage' in msg_content:
            message_type = "sticker"
            sticker = msg_content['stickerMessage']
            content.sticker_url = sticker.get('url', '')
            content.sticker_mimetype = sticker.get('mimetype', '')
            content.sticker_file_length = str(sticker.get('fileLength', ''))
            content.sticker_is_animated = sticker.get('isAnimated', False)
            content.sticker_is_avatar = sticker.get('isAvatar', False)
            content.sticker_is_ai = sticker.get('isAiSticker', False)
            content.sticker_is_lottie = sticker.get('isLottie', False)
            self._extract_common_media_fields(content, sticker)

        # Mensagem de imagem
        elif 'imageMessage' in msg_content:
            message_type = "image"
            image = msg_content['imageMessage']
            content.media_url = image.get('url', '')
            content.media_mimetype = image.get('mimetype', '')
            content.media_file_length = str(image.get('fileLength', ''))
            content.media_caption = image.get('caption', '')
            content.media_height = image.get('height')
            content.media_width = image.get('width')
            content.jpeg_thumbnail = image.get('jpegThumbnail', '')
            self._extract_common_media_fields(content, image)

        # Mensagem de vídeo
        elif 'videoMessage' in msg_content:
            message_type = "video"
            video = msg_content['videoMessage']
            content.media_url = video.get('url', '')
            content.media_mimetype = video.get('mimetype', '')
            content.media_file_length = str(video.get('fileLength', ''))
            content.media_caption = video.get('caption', '')
            self._extract_common_media_fields(content, video)

        # Mensagem de áudio
        elif 'audioMessage' in msg_content:
            message_type = "audio"
            audio = msg_content['audioMessage']
            content.media_url = audio.get('url', '')
            content.media_mimetype = audio.get('mimetype', '')
            content.media_file_length = str(audio.get('fileLength', ''))
            self._extract_common_media_fields(content, audio)

        # Mensagem de documento
        elif 'documentMessage' in msg_content:
            message_type = "document"
            doc = msg_content['documentMessage']
            content.document_url = doc.get('url', '')
            content.document_filename = doc.get('fileName', '')
            content.document_mimetype = doc.get('mimetype', '')
            content.document_file_length = str(doc.get('fileLength', ''))
            content.document_page_count = doc.get('pageCount')

            # Thumbnail do documento
            content.thumbnail_direct_path = doc.get('thumbnailDirectPath', '')
            content.thumbnail_sha256 = doc.get('thumbnailSha256', '')
            content.thumbnail_enc_sha256 = doc.get('thumbnailEncSha256', '')
            content.jpeg_thumbnail = doc.get('jpegThumbnail', '')
            content.thumbnail_height = doc.get('thumbnailHeight')
            content.thumbnail_width = doc.get('thumbnailWidth')

            self._extract_common_media_fields(content, doc)

        # Mensagem de localização
        elif 'locationMessage' in msg_content:
            message_type = "location"
            location = msg_content['locationMessage']
            content.location_latitude = location.get('degreesLatitude')
            content.location_longitude = location.get('degreesLongitude')
            content.location_name = location.get('name', '')
            content.location_address = location.get('address', '')

        # Enquete/Poll - NOVO SUPORTE
        elif 'pollCreationMessageV3' in msg_content:
            message_type = "poll"
            poll = msg_content['pollCreationMessageV3']
            content.poll_name = poll.get('name', '')
            content.poll_selectable_count = poll.get('selectableOptionsCount', 0)

            # Converter opções para JSON
            options = poll.get('options', [])
            poll_options = [opt.get('optionName', '') for opt in options if isinstance(opt, dict)]
            content.poll_options = json.dumps(poll_options, ensure_ascii=False)

        content.message_type = message_type
        session.add(content)

    def _extract_common_media_fields(self, content: MessageContent, media_data: Dict):
        """Extrai campos comuns de mídia"""
        content.file_sha256 = media_data.get('fileSha256', '')
        content.file_enc_sha256 = media_data.get('fileEncSha256', '')
        content.media_key = media_data.get('mediaKey', '')
        content.direct_path = media_data.get('directPath', '')
        content.media_key_timestamp = str(media_data.get('mediaKeyTimestamp', ''))

    def _update_stats(self, session, webhook_data: Dict):
        """Atualiza estatísticas diárias"""
        today = date.today().strftime('%Y-%m-%d')

        # Estatísticas diárias
        daily_stats = session.query(MessageStats).filter_by(date=today).first()
        if not daily_stats:
            daily_stats = MessageStats(date=today)
            session.add(daily_stats)

        # Garantir que os valores não sejam None
        if daily_stats.total_messages is None:
            daily_stats.total_messages = 0
        if daily_stats.messages_sent is None:
            daily_stats.messages_sent = 0
        if daily_stats.messages_received is None:
            daily_stats.messages_received = 0
        if daily_stats.group_messages is None:
            daily_stats.group_messages = 0
        if daily_stats.private_messages is None:
            daily_stats.private_messages = 0

        daily_stats.total_messages += 1

        if webhook_data.get('fromMe'):
            daily_stats.messages_sent += 1
        else:
            daily_stats.messages_received += 1

        if webhook_data.get('isGroup'):
            daily_stats.group_messages += 1
        else:
            daily_stats.private_messages += 1

        # Contar por tipo de mensagem - garantir que não são None
        msg_content = webhook_data.get('msgContent', {})
        if daily_stats.text_count is None:
            daily_stats.text_count = 0
        if daily_stats.sticker_count is None:
            daily_stats.sticker_count = 0
        if daily_stats.image_count is None:
            daily_stats.image_count = 0
        if daily_stats.video_count is None:
            daily_stats.video_count = 0
        if daily_stats.audio_count is None:
            daily_stats.audio_count = 0
        if daily_stats.document_count is None:
            daily_stats.document_count = 0
        if daily_stats.location_count is None:
            daily_stats.location_count = 0
        if daily_stats.poll_count is None:
            daily_stats.poll_count = 0

        if 'conversation' in msg_content:
            daily_stats.text_count += 1
        elif 'stickerMessage' in msg_content:
            daily_stats.sticker_count += 1
        elif 'imageMessage' in msg_content:
            daily_stats.image_count += 1
        elif 'videoMessage' in msg_content:
            daily_stats.video_count += 1
        elif 'audioMessage' in msg_content:
            daily_stats.audio_count += 1
        elif 'documentMessage' in msg_content:
            daily_stats.document_count += 1
        elif 'locationMessage' in msg_content:
            daily_stats.location_count += 1
        elif 'pollCreationMessageV3' in msg_content:
            daily_stats.poll_count += 1

        daily_stats.updated_at = datetime.utcnow()

        # Estatísticas por contato
        self._update_contact_stats(session, webhook_data)

    def _update_contact_stats(self, session, webhook_data: Dict):
        """Atualiza estatísticas por contato"""
        sender_data = webhook_data.get('sender', {})
        if not sender_data or webhook_data.get('isGroup'):
            return

        contact_id = sender_data.get('id', '')
        if not contact_id:
            return

        contact_stats = session.query(ContactStats).filter_by(contact_id=contact_id).first()
        if not contact_stats:
            contact_stats = ContactStats(
                contact_id=contact_id,
                first_message_date=datetime.utcnow(),
                total_messages=0,
                messages_sent_to_them=0,
                messages_received_from_them=0
            )
            session.add(contact_stats)

        # Garantir que os valores não sejam None
        if contact_stats.total_messages is None:
            contact_stats.total_messages = 0
        if contact_stats.messages_sent_to_them is None:
            contact_stats.messages_sent_to_them = 0
        if contact_stats.messages_received_from_them is None:
            contact_stats.messages_received_from_them = 0

        contact_stats.contact_name = sender_data.get('pushName', '')
        contact_stats.last_profile_picture = sender_data.get('profilePicture', '')
        contact_stats.total_messages += 1
        contact_stats.last_message_date = datetime.utcnow()

        # Detectar tipo da mensagem
        msg_content = webhook_data.get('msgContent', {})
        message_type = "unknown"
        if 'conversation' in msg_content:
            message_type = "text"
        elif 'stickerMessage' in msg_content:
            message_type = "sticker"
        elif 'imageMessage' in msg_content:
            message_type = "image"
        elif 'pollCreationMessageV3' in msg_content:
            message_type = "poll"

        contact_stats.last_message_type = message_type

        if webhook_data.get('fromMe'):
            contact_stats.messages_sent_to_them += 1
        else:
            contact_stats.messages_received_from_them += 1

        if sender_data.get('verifiedBizName'):
            contact_stats.is_business = True
            contact_stats.business_name = sender_data.get('verifiedBizName', '')

        contact_stats.updated_at = datetime.utcnow()

    def _update_realtime_stats(self, session, webhook_data: Dict):
        """Atualiza estatísticas em tempo real"""
        try:
            # Total de mensagens
            total_stat = session.query(RealTimeStats).filter_by(stat_key='total_messages').first()
            if total_stat:
                if total_stat.stat_value is None:
                    total_stat.stat_value = 0
                total_stat.stat_value += 1
                total_stat.last_updated = datetime.utcnow()
            else:
                # Criar se não existir
                total_stat = RealTimeStats(stat_key='total_messages', stat_value=1)
                session.add(total_stat)

            # Mensagens de hoje
            today_stat = session.query(RealTimeStats).filter_by(stat_key='messages_today').first()
            if today_stat:
                if today_stat.stat_value is None:
                    today_stat.stat_value = 0
                # Verificar se é um novo dia
                if today_stat.last_updated.date() < datetime.now().date():
                    today_stat.stat_value = 1  # Reset para novo dia
                else:
                    today_stat.stat_value += 1
                today_stat.last_updated = datetime.utcnow()
            else:
                # Criar se não existir
                today_stat = RealTimeStats(stat_key='messages_today', stat_value=1)
                session.add(today_stat)

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar stats tempo real: {e}")

    def get_recent_messages(self, limit: int = 50) -> List[Dict]:
        """Retorna mensagens recentes com informações detalhadas"""
        try:
            with self.get_session() as session:
                query = session.query(WebhookEvent, Sender, MessageContent) \
                    .outerjoin(Sender, WebhookEvent.id == Sender.event_id) \
                    .outerjoin(MessageContent, WebhookEvent.id == MessageContent.event_id) \
                    .order_by(desc(WebhookEvent.created_at)) \
                    .limit(limit)

                results = []
                for event, sender, content in query:
                    message_data = json.loads(event.raw_json)
                    message_data['_db_info'] = {
                        'id': event.id,
                        'message_type': content.message_type if content else 'unknown',
                        'sender_name': sender.push_name if sender else 'Unknown',
                        'saved_at': event.created_at.isoformat()
                    }
                    results.append(message_data)

                return results
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
                    'text_count': stat.text_count,
                    'sticker_count': stat.sticker_count,
                    'image_count': stat.image_count,
                    'video_count': stat.video_count,
                    'audio_count': stat.audio_count,
                    'document_count': stat.document_count,
                    'location_count': stat.location_count,
                    'poll_count': stat.poll_count
                } for stat in stats]
        except Exception as e:
            logger.error(f"❌ Erro ao buscar estatísticas: {e}")
            return []

    def get_realtime_dashboard(self) -> Dict:
        """Retorna dados para dashboard em tempo real"""
        try:
            with self.get_session() as session:
                # Stats básicas
                realtime_stats = {}
                stats = session.query(RealTimeStats).all()
                for stat in stats:
                    realtime_stats[stat.stat_key] = {
                        'value': stat.stat_value,
                        'last_updated': stat.last_updated.isoformat()
                    }

                # Últimas 5 mensagens
                recent_messages = self.get_recent_messages(5)

                # Top 5 contatos hoje
                today = date.today().strftime('%Y-%m-%d')
                top_contacts = session.query(ContactStats) \
                    .filter(func.date(ContactStats.last_message_date) == today) \
                    .order_by(desc(ContactStats.total_messages)) \
                    .limit(5) \
                    .all()

                contact_list = [{
                    'name': contact.contact_name or 'Sem nome',
                    'total_messages': contact.total_messages,
                    'last_message_type': contact.last_message_type
                } for contact in top_contacts]

                return {
                    'stats': realtime_stats,
                    'recent_messages': recent_messages,
                    'top_contacts_today': contact_list,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"❌ Erro ao obter dashboard: {e}")
            return {}

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
                    'last_message_type': contact.last_message_type,
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
                query = session.query(WebhookEvent, Sender, MessageContent) \
                    .outerjoin(Sender, WebhookEvent.id == Sender.event_id) \
                    .outerjoin(MessageContent, WebhookEvent.id == MessageContent.event_id)

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
                    query = query.filter(Sender.sender_id == contact_id)

                # Filtro por tipo de mensagem
                if message_type:
                    query = query.filter(MessageContent.message_type == message_type)

                # Filtro por texto
                if text:
                    query = query.filter(MessageContent.text_content.contains(text))

                results = query.order_by(desc(WebhookEvent.created_at)).limit(limit).all()

                messages = []
                for event, sender, content in results:
                    message_data = json.loads(event.raw_json)
                    message_data['_search_info'] = {
                        'message_type': content.message_type if content else 'unknown',
                        'sender_name': sender.push_name if sender else 'Unknown',
                        'matched_text': text in (content.text_content or '') if text and content else False
                    }
                    messages.append(message_data)

                return messages

        except Exception as e:
            logger.error(f"❌ Erro na busca: {e}")
            return []

    def get_message_types_summary(self) -> Dict:
        """Retorna resumo dos tipos de mensagem"""
        try:
            with self.get_session() as session:
                # Query para contar tipos
                type_counts = session.query(
                    MessageContent.message_type,
                    func.count(MessageContent.id).label('count')
                ).group_by(MessageContent.message_type).all()

                total = sum(count for _, count in type_counts)

                summary = {
                    'total_messages': total,
                    'types': {}
                }

                for msg_type, count in type_counts:
                    percentage = round((count / total * 100), 2) if total > 0 else 0
                    summary['types'][msg_type] = {
                        'count': count,
                        'percentage': percentage
                    }

                return summary
        except Exception as e:
            logger.error(f"❌ Erro ao obter tipos: {e}")
            return {}

    def get_database_info(self) -> Dict:
        """Retorna informações detalhadas sobre o banco de dados"""
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

                # Estatísticas por tipo
                type_summary = self.get_message_types_summary()

                # Stats de hoje
                today = date.today().strftime('%Y-%m-%d')
                today_stats = session.query(MessageStats).filter_by(date=today).first()

                return {
                    'database_path': self.db_path,
                    'total_events': total_events,
                    'total_chats': total_chats,
                    'total_senders': total_senders,
                    'total_message_contents': total_contents,
                    'first_message_date': first_message.created_at.isoformat() if first_message else None,
                    'last_message_date': last_message.created_at.isoformat() if last_message else None,
                    'database_size_mb': round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(
                        self.db_path) else 0,
                    'message_types': type_summary,
                    'today_stats': {
                        'total_today': today_stats.total_messages if today_stats else 0,
                        'sent_today': today_stats.messages_sent if today_stats else 0,
                        'received_today': today_stats.messages_received if today_stats else 0
                    },
                    'schema_version': '2.0.0'
                }
        except Exception as e:
            logger.error(f"❌ Erro ao obter info do banco: {e}")
            return {}

    def process_webhook_batch(self, webhook_list: List[Dict]) -> Dict:
        """Processa múltiplos webhooks em lote para melhor performance"""
        results = {
            'processed': 0,
            'skipped': 0,
            'errors': 0,
            'details': []
        }

        for webhook_data in webhook_list:
            try:
                if self.save_webhook_data(webhook_data):
                    results['processed'] += 1
                    results['details'].append({
                        'message_id': webhook_data.get('messageId', 'unknown'),
                        'status': 'processed'
                    })
                else:
                    results['skipped'] += 1
                    results['details'].append({
                        'message_id': webhook_data.get('messageId', 'unknown'),
                        'status': 'skipped'
                    })
            except Exception as e:
                results['errors'] += 1
                results['details'].append({
                    'message_id': webhook_data.get('messageId', 'unknown'),
                    'status': 'error',
                    'error': str(e)
                })

        return results

    def get_hourly_activity(self, days_back: int = 7) -> List[Dict]:
        """Retorna atividade por hora dos últimos dias"""
        try:
            with self.get_session() as session:
                cutoff_date = datetime.now() - timedelta(days=days_back)

                # Query SQL raw para agrupar por hora
                query = text("""
                    SELECT 
                        strftime('%H', created_at) as hour,
                        COUNT(*) as count
                    FROM webhook_events 
                    WHERE created_at >= :cutoff_date
                    GROUP BY strftime('%H', created_at)
                    ORDER BY hour
                """)

                result = session.execute(query, {'cutoff_date': cutoff_date})

                activity = []
                for row in result:
                    activity.append({
                        'hour': int(row.hour),
                        'count': row.count
                    })

                return activity
        except Exception as e:
            logger.error(f"❌ Erro ao obter atividade por hora: {e}")
            return []

    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """Remove dados antigos do banco"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            with self.get_session() as session:
                # Contar registros que serão removidos
                old_events = session.query(WebhookEvent).filter(
                    WebhookEvent.created_at < cutoff_date
                ).count()

                if old_events > 0:
                    # Remover (cascade vai remover relacionados)
                    session.query(WebhookEvent).filter(
                        WebhookEvent.created_at < cutoff_date
                    ).delete()

                    session.commit()
                    logger.info(f"✅ Removidos {old_events} registros antigos")
                    return old_events

                return 0

        except Exception as e:
            logger.error(f"❌ Erro ao limpar dados: {e}")
            return 0