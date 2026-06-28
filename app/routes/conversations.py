"""
Conversation and chat routes.

/conversations               — list, delete conversations
/conversations/{id}/messages — fetch message history
/conversations/chat          — SSE streaming chat (creates or continues a conversation)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.db.models import BirthProfile, Conversation, User
from app.schemas.conversation import ChatRequest, ConversationResponse, MessageResponse
from app.services.chat import (
    build_chat_system_prompt,
    db_messages_to_langchain,
    format_birth_context,
    stream_conversation,
)

router = APIRouter(tags=["conversations"])


# ---------------------------------------------------------------------------
# Conversation CRUD
# ---------------------------------------------------------------------------

@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def get_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation.messages


# ---------------------------------------------------------------------------
# Chat (SSE) — creates a new conversation or continues an existing one
# ---------------------------------------------------------------------------

@router.post("/conversations/chat")
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.conversation_id is not None:
        conversation = db.query(Conversation).filter(
            Conversation.id == body.conversation_id,
            Conversation.user_id == current_user.id,
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conv_id = conversation.id
        needs_title = conversation.title is None
        history = db_messages_to_langchain(conversation.messages)
    else:
        conv_id = None
        needs_title = True
        history = []

    birth_profile = db.query(BirthProfile).filter(
        BirthProfile.user_id == current_user.id,
        BirthProfile.type == "primary",
    ).first()
    if not birth_profile:
        raise HTTPException(
            status_code=400,
            detail="No primary birth profile found. Please complete onboarding.",
        )

    system_prompt = build_chat_system_prompt(format_birth_context(birth_profile))

    return StreamingResponse(
        stream_conversation(
            user_message=body.message,
            system_prompt=system_prompt,
            history=history,
            conv_id=conv_id,
            needs_title=needs_title,
            user_id=current_user.id,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
