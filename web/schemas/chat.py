from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from web.models import ChatStatus
from web.schemas.message import Message
from web.schemas.user import User


class ChatBase(BaseModel):
    status: ChatStatus = ChatStatus.PENDING


class ChatCreate(ChatBase):
    contact_id: int


class ChatUpdate(BaseModel):
    attendant_id: Optional[int] = None
    status: Optional[ChatStatus] = None


class Chat(ChatBase):
    id: int
    contact_id: int
    attendant_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    messages: List[Message] = []
    attendant: Optional[User] = None

    class Config:
        from_attributes = True