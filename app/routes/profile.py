"""
Profile and birth profile routes.

/profile          — get / update the current user's name
/birth-profiles   — manage primary + partner birth profiles

Rules enforced at application layer:
  - A user can have exactly one profile with type='primary'
  - Primary profile cannot be edited or deleted
  - Partner profiles can be freely created, updated, and deleted
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.base import get_db
from app.db.models import BirthProfile, User
from app.models import BirthChart, KundaliChart, VargaChart
from app.schemas.birth_profile import (
    BirthProfileCreate,
    BirthProfileResponse,
    BirthProfileUpdate,
)
from app.schemas.user import UpdateProfileRequest, UserResponse
from app.services.coord_utils import get_coordinates
from app.services.kundali_chart import (
    calculate_dashamsha,
    calculate_dvadashamsha,
    calculate_navamsa,
    planets_calculation,
)

router = APIRouter(tags=["profile"])

_DEFAULT_COORDS = {"latitude": 23.03, "longitude": 72.62}


class KundaliBundle(BaseModel):
    d1: KundaliChart
    d9: VargaChart
    d10: VargaChart
    d12: VargaChart


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------

@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.name = body.name
    db.commit()
    db.refresh(current_user)
    return current_user


# ---------------------------------------------------------------------------
# Birth profiles
# ---------------------------------------------------------------------------

@router.get("/birth-profiles", response_model=list[BirthProfileResponse])
def list_birth_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(BirthProfile)
        .filter(BirthProfile.user_id == current_user.id)
        .order_by(BirthProfile.created_at)
        .all()
    )


@router.post("/birth-profiles", response_model=BirthProfileResponse, status_code=status.HTTP_201_CREATED)
def create_birth_profile(
    body: BirthProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.type == "primary":
        existing_primary = (
            db.query(BirthProfile)
            .filter(
                BirthProfile.user_id == current_user.id,
                BirthProfile.type == "primary",
            )
            .first()
        )
        if existing_primary:
            raise HTTPException(
                status_code=400,
                detail="A primary profile already exists. Update it instead.",
            )

    profile = BirthProfile(
        user_id=current_user.id,
        type=body.type,
        name=body.name,
        gender=body.gender,
        day=body.day,
        month=body.month,
        year=body.year,
        hour=body.hour,
        minute=body.minute,
        birth_place=body.birth_place,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/birth-profiles/{profile_id}", response_model=BirthProfileResponse)
def update_birth_profile(
    profile_id: uuid.UUID,
    body: BirthProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(BirthProfile).filter(
        BirthProfile.id == profile_id,
        BirthProfile.user_id == current_user.id,
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.type == "primary":
        raise HTTPException(
            status_code=400,
            detail="Primary birth profile cannot be edited.",
        )

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/birth-profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_birth_profile(
    profile_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(BirthProfile).filter(
        BirthProfile.id == profile_id,
        BirthProfile.user_id == current_user.id,
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if profile.type == "primary":
        raise HTTPException(
            status_code=400,
            detail="Primary profile cannot be deleted. Update it instead.",
        )

    db.delete(profile)
    db.commit()


@router.get("/birth-profiles/{profile_id}/kundali", response_model=KundaliBundle)
def get_birth_profile_kundali(
    profile_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(BirthProfile).filter(
        BirthProfile.id == profile_id,
        BirthProfile.user_id == current_user.id,
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    coords = get_coordinates(profile.birth_place) or _DEFAULT_COORDS
    d1 = planets_calculation(BirthChart(
        day=profile.day,
        month=profile.month,
        year=profile.year,
        hour=profile.hour,
        minute=profile.minute,
        second=0,
        latitude=coords["latitude"],
        longitude=coords["longitude"],
    ))

    return KundaliBundle(
        d1=d1,
        d9=calculate_navamsa(d1),
        d10=calculate_dashamsha(d1),
        d12=calculate_dvadashamsha(d1),
    )
