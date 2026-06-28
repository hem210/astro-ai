"""LLM usage tracking — writes one row per user turn to llm_usage."""

import uuid
from datetime import datetime, timezone

import litellm

from app.db.base import SessionLocal
from app.db.models import LLMUsage
from app.logger import get_logger

logger = get_logger("usage")


def write_llm_usage(
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    litellm_model: str,
    input_tokens: int,
    output_tokens: int,
) -> None:
    if not input_tokens and not output_tokens:
        return

    cost = None
    try:
        input_cost, output_cost = litellm.cost_per_token(
            model=litellm_model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
        )
        cost = input_cost + output_cost
    except Exception as exc:
        logger.warning(f"[USAGE] cost calculation failed | model={litellm_model} | {exc}")

    try:
        with SessionLocal() as db:
            db.add(LLMUsage(
                id=uuid.uuid4(),
                user_id=user_id,
                conversation_id=conversation_id,
                model=litellm_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                created_at=datetime.now(timezone.utc),
            ))
            db.commit()
        logger.info(f"[USAGE] recorded | in={input_tokens} out={output_tokens} cost={cost}")
    except Exception as exc:
        logger.error(f"[USAGE] DB write failed | {exc}")
