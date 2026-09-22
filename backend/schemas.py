from typing import Optional

from pydantic import BaseModel, field_validator

from backend.config import settings
from backend.utils.text_utils import sanitize_user_message
from backend.utils.validation_utils import validate_id, validate_english


class ChatResponse(BaseModel):
    chat_id: str
    user_id: str
    reply: str


class ChatRequest(BaseModel):
    chat_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str

    @field_validator("message")
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")

        if len(v) > settings.max_message_length:
            raise ValueError("Message too long")

        cleaned = sanitize_user_message(v)
        if not cleaned:
            raise ValueError("Message contains no usable content")

        if not validate_english(cleaned):
            raise ValueError("Only English messages are allowed")

        return cleaned

    @field_validator("user_id")
    def validate_user_id(cls, v):
        if v is None:
            return v
        if not validate_id(v):
            raise ValueError("Invalid user id format")
        return v

    @field_validator("chat_id")
    def validate_id(cls, v):
        if v is None:
            return v
        if not validate_id(v):
            raise ValueError("Invalid chat id format")
        return v
