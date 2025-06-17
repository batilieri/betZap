from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from permissions import UserRole


# User Schemas
class UserBase(BaseModel):
    nome: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.USER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    role: UserRole
    data_criacao: datetime

    class Config:
        from_attributes = True


# Contact Schemas
class ContactBase(BaseModel):
    nome: str
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    observacoes: Optional[str] = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: int
    user_id: int
    data_criacao: datetime
    ultima_atualizacao: datetime

    class Config:
        from_attributes = True


# Chat Schemas
class ChatBase(BaseModel):
    titulo: str


class ChatCreate(ChatBase):
    contact_id: Optional[int] = None


class ChatUpdate(ChatBase):
    pass


class ChatResponse(ChatBase):
    id: int
    user_id: int
    contact_id: Optional[int] = None
    data_criacao: datetime
    ultima_atividade: datetime

    class Config:
        from_attributes = True


# Message Schemas
class MessageBase(BaseModel):
    conteudo: str
    tipo: str = "text"  # text, image, audio, video, document


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    chat_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


# Chat with Messages
class ChatWithMessages(ChatResponse):
    messages: List[MessageResponse] = []


# Contact with Chats
class ContactWithChats(ContactResponse):
    chats: List[ChatResponse] = []


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_users: int
    total_contacts: int
    total_chats: int
    total_messages: int
    recent_chats: List[ChatResponse]
    recent_contacts: List[ContactResponse]


# Admin Schemas
class UserRoleUpdate(BaseModel):
    role: UserRole


class AdminUserResponse(UserResponse):
    total_contacts: int
    total_chats: int
    total_messages: int