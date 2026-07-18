"""Quota enforcement for per-user question limits."""

import os
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import UserQuota

QUESTION_LIMIT = int(os.getenv("QUESTION_LIMIT", "5"))


def check_and_increment(user_id: uuid.UUID, db: Session) -> None:
    """Raise 403 if the user is at their limit; otherwise increment questions_used."""
    quota = (
        db.query(UserQuota)
        .filter_by(user_id=user_id)
        .with_for_update()
        .first()
    )
    if quota is None:
        quota = UserQuota(user_id=user_id, questions_used=0)
        db.add(quota)

    if quota.questions_used >= QUESTION_LIMIT:
        raise HTTPException(
            status_code=403,
            detail=f"You've used all {QUESTION_LIMIT} questions in this beta. More access coming soon.",
        )

    quota.questions_used += 1
    db.commit()


def get_usage(user_id: uuid.UUID, db: Session) -> tuple[int, int]:
    """Return (questions_used, questions_limit) for the user."""
    quota = db.query(UserQuota).filter_by(user_id=user_id).first()
    return (quota.questions_used if quota else 0, QUESTION_LIMIT)
