from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    conversation_id: str
    user_message: MessageResponse
    ai_message: MessageResponse


class ConversationResponse(BaseModel):
    id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse]

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int
