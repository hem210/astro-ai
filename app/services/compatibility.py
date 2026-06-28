"""
Compatibility service — Ashtakoota score computation and SSE streaming for
partner compatibility analysis. Reuses existing kundali and ashtakoota utilities.
"""

import json
import uuid
from datetime import date, datetime, timezone
from typing import Generator, Optional

from app.db.base import SessionLocal
from app.db.models import BirthProfile, Conversation, Message
from app.logger import get_logger
from app.models import AshtakootaMatchScore, BirthChart
from app.services.agent.astrology_agent import AstrologyAgent
from app.services.agent.config import COMPATIBILITY_SYSTEM_PROMPT
from app.services.ashtakoota_services.calculate_score import calculate_ashtakoota
from app.services.ashtakoota_services.generate_profile import generate_ashtakoota_profile
from app.services.chat import _MONTH_NAMES
from app.services.coord_utils import get_coordinates
from app.services.kundali_chart import planets_calculation

logger = get_logger("compatibility")

_agent: Optional[AstrologyAgent] = None


def _get_agent() -> AstrologyAgent:
    global _agent
    if _agent is None:
        _agent = AstrologyAgent()
    return _agent


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def compute_score_from_birth_details(
    day_a: int, month_a: int, year_a: int, hour_a: int, minute_a: int, birth_place_a: str,
    day_b: int, month_b: int, year_b: int, hour_b: int, minute_b: int, birth_place_b: str,
) -> AshtakootaMatchScore:
    coords_a = get_coordinates(birth_place_a) or {"latitude": 23.03, "longitude": 72.62}
    chart_a = planets_calculation(BirthChart(
        day=day_a, month=month_a, year=year_a, hour=hour_a, minute=minute_a, second=0,
        latitude=coords_a["latitude"], longitude=coords_a["longitude"],
    ))
    profile_a = generate_ashtakoota_profile(
        chart_a.planets["moon"].zodiac, chart_a.planets["moon"].deviation, chart_a.nakshatra
    )

    coords_b = get_coordinates(birth_place_b) or {"latitude": 23.03, "longitude": 72.62}
    chart_b = planets_calculation(BirthChart(
        day=day_b, month=month_b, year=year_b, hour=hour_b, minute=minute_b, second=0,
        latitude=coords_b["latitude"], longitude=coords_b["longitude"],
    ))
    profile_b = generate_ashtakoota_profile(
        chart_b.planets["moon"].zodiac, chart_b.planets["moon"].deviation, chart_b.nakshatra
    )

    return calculate_ashtakoota(profile_a, profile_b)


def compute_score(user_profile: BirthProfile, partner_profile: BirthProfile) -> AshtakootaMatchScore:
    return compute_score_from_birth_details(
        user_profile.day, user_profile.month, user_profile.year,
        user_profile.hour, user_profile.minute, user_profile.birth_place,
        partner_profile.day, partner_profile.month, partner_profile.year,
        partner_profile.hour, partner_profile.minute, partner_profile.birth_place,
    )


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

def _format_profile(profile: BirthProfile) -> str:
    month_name = _MONTH_NAMES[profile.month - 1]
    return (
        f"Name: {profile.name}\n"
        f"Date of Birth: {profile.day} {month_name} {profile.year}\n"
        f"Time of Birth: {profile.hour:02d}:{profile.minute:02d}\n"
        f"Place of Birth: {profile.birth_place}"
    )


def _format_score(score: AshtakootaMatchScore) -> str:
    max_scores = {"nadi": 8, "bhakoota": 7, "gana": 6, "graha_maitri": 5,
                  "yoni": 4, "tara": 3, "vashya": 2, "varna": 1}
    lines = [f"Total: {score.total}/36"]
    for koota, max_val in max_scores.items():
        lines.append(f"- {koota.replace('_', ' ').title()}: {getattr(score, koota)}/{max_val}")
    return "\n".join(lines)


def build_compatibility_system_prompt(
    user_profile: BirthProfile,
    partner_profile: BirthProfile,
    score: AshtakootaMatchScore,
) -> str:
    today = date.today().strftime("%B %d, %Y")
    return (
        COMPATIBILITY_SYSTEM_PROMPT
        + f"\n\n### USER'S BIRTH PROFILE\n{_format_profile(user_profile)}"
        + f"\n\n### PARTNER'S BIRTH PROFILE\n{_format_profile(partner_profile)}"
        + f"\n\n### ASHTAKOOTA COMPATIBILITY SCORE\n{_format_score(score)}"
        + f"\n\n### TODAY'S DATE\nToday is {today}."
    )


# ---------------------------------------------------------------------------
# SSE streaming
# ---------------------------------------------------------------------------

def stream_compatibility_conversation(
    system_prompt: str,
    history: list,
    conv_id: uuid.UUID,
    is_new: bool,
    partner_profile_id: uuid.UUID,
    user_id: uuid.UUID,
    user_message: str,
    title: Optional[str] = None,
) -> Generator[str, None, None]:
    agent = _get_agent()
    collected: list[str] = []

    try:
        for token in agent.stream_tokens(user_message, history, system_prompt):
            collected.append(token)
            yield f"data: {json.dumps({'token': token})}\n\n"
    except Exception as exc:
        logger.error(f"[COMPAT] stream error | conv={conv_id} | {exc}")
        yield f"data: {json.dumps({'error': 'Stream interrupted. Please try again.'})}\n\n"
        return

    full_response = "".join(collected)

    with SessionLocal() as db:
        if is_new:
            conv = Conversation(
                id=conv_id,
                user_id=user_id,
                partner_profile_id=partner_profile_id,
                title=title,
            )
            db.add(conv)
        else:
            conv = db.get(Conversation, conv_id)

        db.add(Message(conversation_id=conv_id, role="user", content=user_message))
        db.add(Message(conversation_id=conv_id, role="assistant", content=full_response))
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()

    yield f"data: {json.dumps({'done': True, 'conversation_id': str(conv_id)})}\n\n"
