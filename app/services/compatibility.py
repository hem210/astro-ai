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
    groom, bride = (user_profile, partner_profile) if user_profile.gender == "male" else (partner_profile, user_profile)
    return compute_score_from_birth_details(
        groom.day, groom.month, groom.year, groom.hour, groom.minute, groom.birth_place,
        bride.day, bride.month, bride.year, bride.hour, bride.minute, bride.birth_place,
    )


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------

def _get_ashtakoota_profile(profile: BirthProfile):
    coords = get_coordinates(profile.birth_place) or {"latitude": 23.03, "longitude": 72.62}
    chart = planets_calculation(BirthChart(
        day=profile.day, month=profile.month, year=profile.year,
        hour=profile.hour, minute=profile.minute, second=0,
        latitude=coords["latitude"], longitude=coords["longitude"],
    ))
    return generate_ashtakoota_profile(
        chart.planets["moon"].zodiac, chart.planets["moon"].deviation, chart.nakshatra
    )


def _format_birth_profile(profile: BirthProfile) -> str:
    month_name = _MONTH_NAMES[profile.month - 1]
    return (
        f"Name: {profile.name}\n"
        f"Date of Birth: {profile.day} {month_name} {profile.year}\n"
        f"Time of Birth: {profile.hour:02d}:{profile.minute:02d}\n"
        f"Place of Birth: {profile.birth_place}"
    )


def _format_ashtakoota_profile(ap) -> str:
    return (
        f"Moon Sign: {ap.moon_zodiac}\n"
        f"Nakshatra: {ap.nakshatra}\n"
        f"Nadi: {ap.nadi}\n"
        f"Gana: {ap.gana}\n"
        f"Yoni: {ap.yoni}\n"
        f"Graha Maitri: {ap.graha_maitri}\n"
        f"Vashya: {ap.vashya}\n"
        f"Varna: {ap.varna}"
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
    user_ap = _get_ashtakoota_profile(user_profile)
    partner_ap = _get_ashtakoota_profile(partner_profile)
    user_label = "GROOM" if user_profile.gender == "male" else "BRIDE"
    partner_label = "GROOM" if partner_profile.gender == "male" else "BRIDE"
    return (
        COMPATIBILITY_SYSTEM_PROMPT
        + f"\n\n### {user_label}'S BIRTH PROFILE\n{_format_birth_profile(user_profile)}\n{_format_ashtakoota_profile(user_ap)}"
        + f"\n\n### {partner_label}'S BIRTH PROFILE\n{_format_birth_profile(partner_profile)}\n{_format_ashtakoota_profile(partner_ap)}"
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
    save_user_message: bool = True,
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

        if save_user_message:
            db.add(Message(conversation_id=conv_id, role="user", content=user_message))
        db.add(Message(conversation_id=conv_id, role="assistant", content=full_response))
        conv.updated_at = datetime.now(timezone.utc)
        db.commit()

    yield f"data: {json.dumps({'done': True, 'conversation_id': str(conv_id)})}\n\n"
