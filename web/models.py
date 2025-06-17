from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from permissions import UserRole
import enum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    senha = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos
    contacts = relationship("Contact", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    telefone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    observacoes = Column(Text, nullable=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    ultima_atualizacao = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Foreign Key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="contacts")
    chats = relationship("Chat", back_populates="contact")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())
    ultima_atividade = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)

    # Relacionamentos
    user = relationship("User", back_populates="chats")
    contact = relationship("Contact", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conteudo = Column(Text, nullable=False)
    tipo = Column(String(20), default="text", nullable=False)  # text, image, audio, video, document
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign Key
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)

    # Relacionamentos
    chat = relationship("Chat", back_populates="messages")