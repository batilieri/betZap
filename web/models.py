from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base
import uuid
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True, index=True)
    avatar_url = Column(String(500), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(20), default=UserRole.USER, index=True)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    sent_messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    received_messages = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient")
    chats_created = relationship("Chat", foreign_keys="Chat.created_by", back_populates="creator")
    chat_participants = relationship("ChatParticipant", back_populates="user")
    contacts_owner = relationship("Contact", foreign_keys="Contact.owner_id", back_populates="owner")
    contacts_contact = relationship("Contact", foreign_keys="Contact.contact_id", back_populates="contact")

    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_role_active', 'role', 'is_active'),
    )


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=True)  # Para grupos
    description = Column(Text, nullable=True)
    is_group = Column(Boolean, default=False, index=True)
    avatar_url = Column(String(500), nullable=True)

    # Configurações
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="chats_created")
    participants = relationship("ChatParticipant", back_populates="chat", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_chat_active_updated', 'is_active', 'last_message_at'),
    )


class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Permissões
    can_send_messages = Column(Boolean, default=True)
    can_add_participants = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # Status
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)
    last_read_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    chat = relationship("Chat", back_populates="participants")
    user = relationship("User", back_populates="chat_participants")

    __table_args__ = (
        UniqueConstraint('chat_id', 'user_id', name='uq_chat_user'),
        Index('idx_participant_chat_user', 'chat_id', 'user_id'),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)

    # Conteúdo
    content = Column(Text, nullable=True)
    message_type = Column(String(20), default=MessageType.TEXT, index=True)
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)

    # Relacionamentos
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)

    # Status
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False, index=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")
    reply_to = relationship("Message", remote_side=[id])

    __table_args__ = (
        Index('idx_message_chat_created', 'chat_id', 'created_at'),
        Index('idx_message_sender_created', 'sender_id', 'created_at'),
        Index('idx_message_deleted_created', 'is_deleted', 'created_at'),
    )


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    contact_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Informações personalizadas
    custom_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False, index=True)
    is_blocked = Column(Boolean, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="contacts_owner")
    contact = relationship("User", foreign_keys=[contact_id], back_populates="contacts_contact")

    __table_args__ = (
        UniqueConstraint('owner_id', 'contact_id', name='uq_owner_contact'),
        Index('idx_contact_owner_favorite', 'owner_id', 'is_favorite'),
        Index('idx_contact_owner_blocked', 'owner_id', 'is_blocked'),
    )