from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chatbot import (
    ChatMessageRequest,
    ChatResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from app.services.chatbot import (
    delete_conversation,
    get_conversation,
    list_conversations,
    send_message,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.post("/chatbot", response_model=ChatResponse)
def post_chatbot(
    request: ChatMessageRequest,
    http_request: Request,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Send a message to the AI chatbot.

    Provide a conversation_id to continue an existing conversation,
    or omit it to start a new one.
    """
    try:
        conversation, user_msg, ai_msg = send_message(
            db,
            message=request.message,
            conversation_id=request.conversation_id,
            authorization=http_request.headers.get("authorization"),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ChatResponse(
        conversation_id=conversation.id,
        user_message=MessageResponse.model_validate(user_msg),
        ai_message=MessageResponse.model_validate(ai_msg),
    )


@router.get("/chatbot", response_model=ConversationListResponse)
def get_chatbot(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ConversationListResponse:
    """List all conversations with their messages."""
    conversations, total = list_conversations(db, limit=limit, offset=offset)
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
    )


@router.get("/chatbot/{conversation_id}", response_model=ConversationResponse)
def get_chatbot_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """Get a single conversation with its full message history."""
    conversation = get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conversation)


@router.delete("/chatbot/{conversation_id}", status_code=204)
def delete_chatbot_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
) -> None:
    """Delete a conversation and all its messages."""
    if not delete_conversation(db, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
