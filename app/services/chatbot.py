from __future__ import annotations

from google.genai import types
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.gemini import client as gemini_client
from app.db.models import Conversation, Message


def _build_history(messages: list[Message]) -> list[types.Content]:
    """Convert stored messages into Gemini Content objects for context."""
    history: list[types.Content] = []
    for msg in messages:
        history.append(
            types.Content(
                role=msg.role,
                parts=[types.Part(text=msg.content)],
            )
        )
    return history


def send_message(db: Session, *, message: str, conversation_id: str | None) -> tuple[Conversation, Message, Message]:
    """Send a user message and get an AI response.

    If conversation_id is provided, continues an existing conversation.
    Otherwise creates a new one.
    """
    if conversation_id:
        conversation = db.get(Conversation, conversation_id)
        if not conversation:
            raise LookupError(f"Conversation {conversation_id} not found")
    else:
        conversation = Conversation(title=message[:120])
        db.add(conversation)
        db.flush()

    # Persist the user message.
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=message,
    )
    db.add(user_msg)
    db.flush()

    # Build history from previous messages (excluding the one we just added).
    history = _build_history(
        [m for m in conversation.messages if m.id != user_msg.id]
    )

    # Call Gemini with conversation history.
    chat = gemini_client.chats.create(
        model=settings.GEMINI_MODEL,
        history=history,
    )
    response = chat.send_message(message)
    ai_text = response.text or ""

    # Persist the AI response.
    ai_msg = Message(
        conversation_id=conversation.id,
        role="model",
        content=ai_text,
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(conversation)
    db.refresh(user_msg)
    db.refresh(ai_msg)

    return conversation, user_msg, ai_msg


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    return db.get(Conversation, conversation_id)


def list_conversations(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Conversation], int]:
    count_stmt = select(Conversation)
    total = len(db.execute(count_stmt.with_only_columns(Conversation.id)).all())

    stmt = (
        select(Conversation)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    conversations = list(db.execute(stmt).scalars().all())
    return conversations, total


def delete_conversation(db: Session, conversation_id: str) -> bool:
    conversation = db.get(Conversation, conversation_id)
    if not conversation:
        return False
    db.delete(conversation)
    db.commit()
    return True
