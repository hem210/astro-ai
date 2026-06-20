"""
Conversation and chat routes.

/conversations               — list, create, delete conversations
/conversations/{id}/messages — fetch message history
/conversations/{id}/chat     — SSE streaming chat
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


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = Conversation(user_id=current_user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


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
# Chat (SSE)
# ---------------------------------------------------------------------------

@router.post("/conversations/{conversation_id}/chat")
def chat(
    conversation_id: uuid.UUID,
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    birth_profile = db.query(BirthProfile).filter(
        BirthProfile.user_id == current_user.id,
        BirthProfile.type == "primary",
    ).first()
    if not birth_profile:
        raise HTTPException(
            status_code=400,
            detail="No primary birth profile found. Please complete onboarding.",
        )

    return StreamingResponse(
        stream_conversation(
            user_message=body.message,
            birth_context=format_birth_context(birth_profile),
            history=db_messages_to_langchain(conversation.messages),
            conv_id=conversation.id,
            needs_title=conversation.title is None,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
