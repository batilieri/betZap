#!/usr/bin/env python3
"""
Modelos do banco de dados para o sistema de webhook do WhatsApp
SQLite com SQLAlchemy para máxima performance e simplicidade
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()


class WebhookEvent(Base):
    """Tabela principal para eventos de webhook"""
    __tablename__ = 'webhook_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)  # webhookDelivery, etc
    instance_id = Column(String(100), nullable=False, index=True)
    connected_phone = Column(String(20), nullable=False, index=True)
    message_id = Column(String(100), unique=True, index=True)
    from_me = Column(Boolean, default=False, index=True)
    from_api = Column(Boolean, default=False)
    is_group = Column(Boolean, default=False, index=True)
    moment = Column(Integer, nullable=False)  # timestamp unix
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    raw_json = Column(Text)  # JSON completo para backup

    # Relacionamentos
    chat = relationship("Chat", back_populates="events", uselist=False)
    sender = relationship("Sender", back_populates="events", uselist=False)
    message_content = relationship("MessageContent", back_populates="event", uselist=False)


class Chat(Base):
    """Tabela para informações do chat"""
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('webhook_events.id'), unique=True)
    chat_id = Column(String(20), nullable=False, index=True)
    profile_picture = Column(Text)
    is_group = Column(Boolean, default=False)
    group_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    events = relationship("WebhookEvent", back_populates="chat")


class Sender(Base):
    """Tabela para informações do remetente"""
    __tablename__ = 'senders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('webhook_events.id'), unique=True)
    sender_id = Column(String(20), nullable=False, index=True)
    profile_picture = Column(Text)
    push_name = Column(String(200))
    verified_biz_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    events = relationship("WebhookEvent", back_populates="sender")


class MessageContent(Base):
    """Tabela para conteúdo das mensagens"""
    __tablename__ = 'message_contents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('webhook_events.id'), unique=True)
    message_type = Column(String(50), nullable=False, index=True)  # text, sticker, image, etc

    # Campos para mensagem de texto
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

    # Campos para documento
    document_url = Column(Text)
    document_filename = Column(String(200))
    document_mimetype = Column(String(50))
    document_file_length = Column(String(20))

    # Campos para localização
    location_latitude = Column(String(50))
    location_longitude = Column(String(50))
    location_name = Column(String(200))
    location_address = Column(Text)

    # Campos de hash e criptografia
    file_sha256 = Column(String(100))
    file_enc_sha256 = Column(String(100))
    media_key = Column(String(100))
    direct_path = Column(Text)
    media_key_timestamp = Column(String(20))

    # Context info
    message_secret = Column(String(100))

    # JSON completo do conteúdo para casos especiais
    raw_content_json = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    event = relationship("WebhookEvent", back_populates="message_content")


class MessageStats(Base):
    """Tabela para estatísticas rápidas"""
    __tablename__ = 'message_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, index=True)  # YYYY-MM-DD
    total_messages = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)  # from_me = True
    messages_received = Column(Integer, default=0)  # from_me = False
    group_messages = Column(Integer, default=0)
    private_messages = Column(Integer, default=0)
    sticker_count = Column(Integer, default=0)
    text_count = Column(Integer, default=0)
    media_count = Column(Integer, default=0)
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
    updated_at = Column(DateTime, default=datetime.utcnow)


# Configuração do banco
def create_database_engine(db_path="whatsapp_webhook.db"):
    """Cria e configura o engine do banco de dados"""
    engine = create_engine(
        f'sqlite:///{db_path}',
        echo=False,  # Mude para True para debug SQL
        pool_pre_ping=True,
        connect_args={
            'check_same_thread': False,
            'timeout': 20
        }
    )
    return engine


def create_session_factory(engine):
    """Cria factory de sessões"""
    Session = sessionmaker(bind=engine)
    return Session


def init_database(db_path="whatsapp_webhook.db"):
    """Inicializa o banco de dados criando todas as tabelas"""
    engine = create_database_engine(db_path)
    Base.metadata.create_all(engine)
    return engine, create_session_factory(engine)