"""
Best-match route.

GET /best-matches
  Returns all 36 rashi-nakshatra combinations scored against the current user's
  primary birth profile, sorted by Ashtakoota score descending.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.db.models import BirthProfile, User
from app.models import AshtakootaMatchScore, BirthChart
from app.services.ashtakoota_services.generate_profile import generate_ashtakoota_profile
from app.services.coord_utils import get_coordinates
from app.services.kundali_chart import planets_calculation
from app.services.match_finder import find_best_matches


class DoshaInfo(BaseModel):
    cancelled: bool
    cancellation_reason: str | None


class MatchResult(BaseModel):
    rashi: str
    nakshatra: str
    syllables: list[str]
    score: AshtakootaMatchScore
    nadi_dosha: DoshaInfo | None
    bhakoota_dosha: DoshaInfo | None

router = APIRouter(tags=["matches"])

_DEFAULT_COORDS = {"latitude": 23.03, "longitude": 72.62}


@router.get("/best-matches", response_model=list[MatchResult])
def get_best_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    primary = (
        db.query(BirthProfile)
        .filter_by(user_id=current_user.id, type="primary")
        .first()
    )
    if not primary:
        raise HTTPException(status_code=400, detail="No primary birth profile found. Please complete onboarding.")

    coords = get_coordinates(primary.birth_place) or _DEFAULT_COORDS
    chart = planets_calculation(BirthChart(
        day=primary.day,
        month=primary.month,
        year=primary.year,
        hour=primary.hour,
        minute=primary.minute,
        second=0,
        latitude=coords["latitude"],
        longitude=coords["longitude"],
    ))

    person_profile = generate_ashtakoota_profile(
        chart.moon_zodiac,
        chart.moon_deviate,
        chart.nakshatra,
    )

    matches = find_best_matches(person_profile, primary.gender)
    return matches
