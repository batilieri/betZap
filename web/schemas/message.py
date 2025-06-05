from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from web.models import MessageType


class MessageBase(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT
    media_url: Optional[str] = None


class MessageCreate(MessageBase):
    chat_id: int
    is_from_customer: bool = True


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    read_at: Optional[datetime] = None


class Message(MessageBase):
    id: int
    chat_id: int
    whatsapp_id: str
    is_from_customer: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True
