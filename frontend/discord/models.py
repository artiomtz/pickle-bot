from datetime import datetime
from typing import List

from pydantic import BaseModel


class BackendReply(BaseModel):
    chat_id: str
    user_id: str
    reply: str


class BackendMessage(BaseModel):
    user_id: str
    role: str
    content: str
    created_at: datetime


class MessageBatch(BaseModel):
    messages: List[BackendMessage]
