"""
Compatibility routes.

GET  /compatibility/{partner_id}          — score + latest conversation + messages
POST /compatibility/{partner_id}/analyze  — SSE stream; generates new analysis
POST /compatibility/{partner_id}/chat     — SSE stream; follow-up on latest conversation
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.db.models import BirthProfile, Conversation, User
from app.models import AshtakootaMatchScore
from app.schemas.compatibility import (
    CompatibilityChatRequest,
    CompatibilityStateResponse,
)
from app.services.chat import db_messages_to_langchain
from app.services.compatibility import (
    build_compatibility_system_prompt,
    compute_score,
    stream_compatibility_conversation,
)

_INITIAL_ANALYSIS_PROMPT = (
    "Generate the compatibility analysis for this pairing based on their Ashtakoota score "
    "and birth profiles. Follow the tone and structure guidelines in your instructions."
)

router = APIRouter(prefix="/compatibility", tags=["compatibility"])


def _get_partner(partner_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> BirthProfile:
    partner = db.query(BirthProfile).filter_by(id=partner_id, user_id=user_id, type="partner").first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner profile not found")
    return partner



def _latest_conversation(partner_id: uuid.UUID, user_id: uuid.UUID, db: Session) -> Conversation | None:
    return (
        db.query(Conversation)
        .filter_by(user_id=user_id, partner_profile_id=partner_id)
        .order_by(Conversation.created_at.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# GET — current compatibility state
# ---------------------------------------------------------------------------

@router.get("/{partner_id}", response_model=CompatibilityStateResponse)
def get_compatibility(
    partner_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    partner = _get_partner(partner_id, current_user.id, db)
    conv = _latest_conversation(partner_id, current_user.id, db)

    score = None
    if partner.compatibility_score:
        score = partner.compatibility_score

    return CompatibilityStateResponse(
        score=score,
        conversation_id=conv.id if conv else None,
        messages=conv.messages if conv else [],
    )


# ---------------------------------------------------------------------------
# POST /analyze — generate new compatibility analysis (SSE)
# ---------------------------------------------------------------------------

@router.post("/{partner_id}/analyze")
def analyze(
    partner_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    partner = _get_partner(partner_id, current_user.id, db)
    user_profile = db.query(BirthProfile).filter_by(user_id=current_user.id, type="primary").first()
    if not user_profile:
        raise HTTPException(status_code=400, detail="No primary birth profile found")

    score = compute_score(user_profile, partner)

    # Persist score on partner profile
    partner.compatibility_score = score.model_dump()
    db.commit()

    system_prompt = build_compatibility_system_prompt(user_profile, partner, score)
    conv_id = uuid.uuid4()
    title = f"{partner.name} — compatibility"

    return StreamingResponse(
        stream_compatibility_conversation(
            system_prompt=system_prompt,
            history=[],
            conv_id=conv_id,
            is_new=True,
            partner_profile_id=partner_id,
            user_id=current_user.id,
            user_message=_INITIAL_ANALYSIS_PROMPT,
            title=title,
            save_user_message=False,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# POST /chat — follow-up messages on latest compatibility conversation (SSE)
# ---------------------------------------------------------------------------

@router.post("/{partner_id}/chat")
def chat(
    partner_id: uuid.UUID,
    body: CompatibilityChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    partner = _get_partner(partner_id, current_user.id, db)
    user_profile = db.query(BirthProfile).filter_by(user_id=current_user.id, type="primary").first()
    if not user_profile:
        raise HTTPException(status_code=400, detail="No primary birth profile found")

    conv = _latest_conversation(partner_id, current_user.id, db)
    if not conv:
        raise HTTPException(status_code=404, detail="No analysis found. Generate an analysis first.")

    if not partner.compatibility_score:
        raise HTTPException(status_code=400, detail="Compatibility score not found")

    score = AshtakootaMatchScore(**partner.compatibility_score)
    system_prompt = build_compatibility_system_prompt(user_profile, partner, score)
    history = db_messages_to_langchain(conv.messages)

    return StreamingResponse(
        stream_compatibility_conversation(
            system_prompt=system_prompt,
            history=history,
            conv_id=conv.id,
            is_new=False,
            partner_profile_id=partner_id,
            user_id=current_user.id,
            user_message=body.message,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
