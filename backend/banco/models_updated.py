#!/usr/bin/env python3
"""
Modelos atualizados do banco de dados para WhatsApp webhooks
SQLite com SQLAlchemy otimizado para os novos tipos de mensagem
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()


class WebhookEvent(Base):
    """Tabela principal para eventos de webhook"""
    __tablename__ = 'webhook_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)
    instance_id = Column(String(100), nullable=False, index=True)
    connected_phone = Column(String(20), nullable=False, index=True)
    message_id = Column(String(100), unique=True, index=True)
    from_me = Column(Boolean, default=False, index=True)
    from_api = Column(Boolean, default=False)
    is_group = Column(Boolean, default=False, index=True)
    moment = Column(Integer, nullable=False, index=True)  # timestamp unix
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    raw_json = Column(Text)  # JSON completo para backup

    # Relacionamentos
    chat = relationship("Chat", back_populates="event", uselist=False, cascade="all, delete-orphan")
    sender = relationship("Sender", back_populates="event", uselist=False, cascade="all, delete-orphan")
    message_content = relationship("MessageContent", back_populates="event", uselist=False,
                                   cascade="all, delete-orphan")
    message_medias = relationship("MessageMedia", back_populates="event", cascade="all, delete-orphan")

class Chat(Base):
    """Tabela para informações do chat"""
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('webhook_events.id', ondelete='CASCADE'), unique=True)
    chat_id = Column(String(20), nullable=False, index=True)
    profile_picture = Column(Text)
    is_group = Column(Boolean, default=False)
    group_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    event = relationship("WebhookEvent", back_populates="chat")


class Sender(Base):
    """Tabela para informações do remetente"""
    __tablename__ = 'senders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('webhook_events.id', ondelete='CASCADE'), unique=True)
    sender_id = Column(String(20), nullable=False, index=True)
    profile_picture = Column(Text)
    push_name = Column(String(200), index=True)
    verified_biz_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    event = relationship("WebhookEvent", back_populates="sender")


class MessageContent(Base):
    """Tabela para conteúdo das mensagens - ATUALIZADA"""
    __tablename__ = 'message_contents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('webhook_events.id', ondelete='CASCADE'), unique=True)
    message_type = Column(String(50), nullable=False, index=True)

    # Campos para mensagem de texto/emoji
    text_content = Column(Text)

    # Campos para sticker
    sticker_url = Column(Text)
    sticker_mimetype = Column(String(50))
    sticker_file_length = Column(String(20))
    sticker_is_animated = Column(Boolean)
    sticker_is_avatar = Column(Boolean)
    sticker_is_ai = Column(Boolean)
    sticker_is_lottie = Column(Boolean)

    # Campos para mídia (imagem, vídeo, áudio)
    media_url = Column(Text)
    media_mimetype = Column(String(50))
    media_file_length = Column(String(20))
    media_caption = Column(Text)
    media_height = Column(Integer)
    media_width = Column(Integer)

    # Campos para documento
    document_url = Column(Text)
    document_filename = Column(String(200))
    document_mimetype = Column(String(50))
    document_file_length = Column(String(20))
    document_page_count = Column(Integer)

    # Campos para localização
    location_latitude = Column(Float)
    location_longitude = Column(Float)
    location_name = Column(String(200))
    location_address = Column(Text)

    # Campos para enquete/poll - NOVO
    poll_name = Column(String(200))
    poll_options = Column(Text)  # JSON array das opções
    poll_selectable_count = Column(Integer)

    # Campos de hash e criptografia
    file_sha256 = Column(String(100))
    file_enc_sha256 = Column(String(100))
    media_key = Column(String(100))
    direct_path = Column(Text)
    media_key_timestamp = Column(String(20))

    # Thumbnails
    jpeg_thumbnail = Column(Text)  # base64
    thumbnail_direct_path = Column(Text)
    thumbnail_sha256 = Column(String(100))
    thumbnail_enc_sha256 = Column(String(100))
    thumbnail_height = Column(Integer)
    thumbnail_width = Column(Integer)

    # Context info
    message_secret = Column(String(100))
    device_list_metadata = Column(Text)  # JSON do metadata

    # JSON completo do conteúdo
    raw_content_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    event = relationship("WebhookEvent", back_populates="message_content")


class MessageStats(Base):
    """Tabela para estatísticas diárias"""
    __tablename__ = 'message_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, index=True)  # YYYY-MM-DD
    total_messages = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    group_messages = Column(Integer, default=0)
    private_messages = Column(Integer, default=0)

    # Contadores por tipo
    text_count = Column(Integer, default=0)
    sticker_count = Column(Integer, default=0)
    image_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)
    audio_count = Column(Integer, default=0)
    document_count = Column(Integer, default=0)
    location_count = Column(Integer, default=0)
    poll_count = Column(Integer, default=0)  # NOVO

    updated_at = Column(DateTime, default=datetime.utcnow)


class ContactStats(Base):
    """Tabela para estatísticas por contato"""
    __tablename__ = 'contact_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(String(20), unique=True, index=True)
    contact_name = Column(String(200))
    last_profile_picture = Column(Text)
    total_messages = Column(Integer, default=0)
    messages_sent_to_them = Column(Integer, default=0)
    messages_received_from_them = Column(Integer, default=0)
    last_message_date = Column(DateTime)
    first_message_date = Column(DateTime)
    is_business = Column(Boolean, default=False)
    business_name = Column(String(200))

    # Novos campos de atividade
    last_message_type = Column(String(50))
    favorite_message_type = Column(String(50))  # tipo mais usado

    updated_at = Column(DateTime, default=datetime.utcnow)


class RealTimeStats(Base):
    """Tabela para estatísticas em tempo real"""
    __tablename__ = 'realtime_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_key = Column(String(50), unique=True, index=True)
    stat_value = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)


class MessageMedia(Base):
    """Tabela para relacionar mensagens com suas mídias baixadas"""
    __tablename__ = 'whatsapp_message_medias'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('webhook_events.id', ondelete='CASCADE'), nullable=False, index=True)
    media_path = Column(Text, nullable=False)
    media_type = Column(String(50), nullable=False, index=True)  # image, video, audio, document, sticker
    mimetype = Column(String(50))
    file_size = Column(Integer)
    download_status = Column(String(20), default='pending')  # pending, success, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamento
    event = relationship("WebhookEvent", back_populates="message_medias")


# Configuração do banco
def create_database_engine(db_path="whatsapp_webhook_realtime.db"):
    """Cria e configura o engine do banco de dados"""
    engine = create_engine(
        f'sqlite:///{db_path}',
        echo=False,
        pool_pre_ping=True,
        connect_args={
            'check_same_thread': False,
            'timeout': 30,
            'isolation_level': None  # Autocommit mode
        }
    )
    return engine


def create_session_factory(engine):
    """Cria factory de sessões"""
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    return Session


def init_database(db_path="whatsapp_webhook_realtime.db"):
    """Inicializa o banco de dados criando todas as tabelas"""
    engine = create_database_engine(db_path)
    Base.metadata.create_all(engine)

    # Criar estatísticas iniciais
    Session = create_session_factory(engine)
    session = Session()

    try:
        # Verificar se já existem stats
        existing_stats = session.query(RealTimeStats).first()
        if not existing_stats:
            initial_stats = [
                RealTimeStats(stat_key='total_messages', stat_value=0),
                RealTimeStats(stat_key='messages_today', stat_value=0),
                RealTimeStats(stat_key='active_contacts', stat_value=0),
                RealTimeStats(stat_key='groups_active', stat_value=0),
            ]
            session.add_all(initial_stats)
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"⚠️ Erro ao criar stats iniciais: {e}")
    finally:
        session.close()

    return engine, create_session_factory(engine)


def get_database_schema_version():
    """Retorna versão do schema do banco"""
    return "2.0.0"
