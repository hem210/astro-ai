"""
Chat service — orchestrates LLM streaming, SSE formatting, and message persistence.

This is the layer between the HTTP route and the agent. If LangGraph's streaming
API changes, stream_conversation() is the likely change point alongside
AstrologyAgent.stream_tokens().
"""

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Generator, Optional

from langchain_core.messages import AIMessage, HumanMessage

from app.db.base import SessionLocal
from app.db.models import BirthProfile, Conversation, Message
from app.logger import get_logger
from app.services.agent.astrology_agent import AstrologyAgent

logger = get_logger("chat")

DEV_MOCK = os.getenv("DEV_MOCK", "false").lower() == "true"

_agent: Optional[AstrologyAgent] = None


def get_agent() -> AstrologyAgent:
    global _agent
    if _agent is None:
        _agent = AstrologyAgent()
    return _agent


_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

def format_birth_context(profile: BirthProfile) -> str:
    month_name = _MONTH_NAMES[profile.month - 1]
    return (
        f"Name: {profile.name}\n"
        f"Date of Birth: {profile.day} {month_name} {profile.year}\n"
        f"Time of Birth: {profile.hour:02d}:{profile.minute:02d}\n"
        f"Place of Birth: {profile.birth_place}"
    )


def db_messages_to_langchain(messages: list[Message], window: int = 20) -> list:
    result = []
    for msg in messages[-window:]:
        if msg.role == "user":
            result.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            result.append(AIMessage(content=msg.content))
    return result


_MOCK_RESPONSE = (
    "Based on your birth chart, Jupiter is currently transiting your 9th house, "
    "bringing expansion and opportunity in areas of higher learning and long-distance travel. "
    "Your Moon in Rohini nakshatra suggests a strong emotional connection to comfort and beauty. "
    "The current Vimshottari dasha period indicates a time of **gradual growth** — "
    "patience will be your greatest asset over the next 18 months.\n\n"
    "Key transits to watch:\n"
    "- **Saturn** aspects your natal Sun, calling for discipline in your career\n"
    "- **Venus** in your 7th house favours relationships and partnerships\n"
    "- The upcoming **Amavasya** on the 30th is an auspicious time for new beginnings"
)


def _mock_stream(
    conv_id: uuid.UUID,
    user_id: uuid.UUID,
    user_message: str,
    needs_title: bool,
    is_new: bool,
) -> Generator[str, None, None]:
    """Streams a static response with realistic delays. No LLM call is made."""
    logger.info(f"[CHAT] DEV_MOCK active — skipping LLM | conv={conv_id}")

    # Simulate the thinking delay before first token
    time.sleep(4)

    words = _MOCK_RESPONSE.split(" ")
    for i, word in enumerate(words):
        token = word if i == len(words) - 1 else word + " "
        yield f"data: {json.dumps({'token': token})}\n\n"
        time.sleep(0.06)

    with SessionLocal() as db:
        if is_new:
            conv = Conversation(id=conv_id, user_id=user_id)
            db.add(conv)
        else:
            conv = db.get(Conversation, conv_id)
        db.add(Message(conversation_id=conv_id, role="user", content=user_message))
        db.add(Message(conversation_id=conv_id, role="assistant", content=_MOCK_RESPONSE))
        conv.updated_at = datetime.now(timezone.utc)
        if needs_title:
            conv.title = "Mock conversation"
        db.commit()

    yield f"data: {json.dumps({'done': True, 'conversation_id': str(conv_id)})}\n\n"


def stream_conversation(
    user_message: str,
    birth_context: str,
    history: list,
    conv_id: Optional[uuid.UUID],
    needs_title: bool,
    user_id: uuid.UUID,
) -> Generator[str, None, None]:
    """
    SSE generator for a single chat turn.

    For new conversations (conv_id=None), a UUID is generated immediately but
    the DB row is only committed on success — no orphan rows on failure.

    Final SSE event is always {"done": true, "conversation_id": "..."} so the
    frontend can update the URL after confirming the turn was persisted.
    """
    is_new = conv_id is None
    if is_new:
        conv_id = uuid.uuid4()

    if DEV_MOCK:
        yield from _mock_stream(conv_id, user_id, user_message, needs_title, is_new)
        return

    agent = get_agent()
    collected: list[str] = []

    try:
        for token in agent.stream_tokens(user_message, history, birth_context):
            collected.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"
    except Exception as exc:
        logger.error(f"[CHAT] stream error | conv={conv_id} | {exc}")
        yield f"data: {json.dumps({'error': 'Stream interrupted. Please try again.'})}\n\n"
        return

    full_response = "".join(collected)

    with SessionLocal() as db:
        if is_new:
            conv = Conversation(id=conv_id, user_id=user_id)
            db.add(conv)
        else:
            conv = db.get(Conversation, conv_id)

        db.add(Message(conversation_id=conv_id, role="user", content=user_message))
        db.add(Message(conversation_id=conv_id, role="assistant", content=full_response))

        conv.updated_at = datetime.now(timezone.utc)

        if needs_title:
            try:
                conv.title = agent.generate_title(user_message)
            except Exception as exc:
                logger.warning(f"[CHAT] title generation failed | {exc}")

        db.commit()

    yield f"data: {json.dumps({'done': True, 'conversation_id': str(conv_id)})}\n\n"
