"""Pydantic schemas for birth profile endpoints."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BirthProfileCreate(BaseModel):
    type: Literal["primary", "partner"]
    name: str
    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=1800, le=2399)
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    birth_place: str


class BirthProfileUpdate(BaseModel):
    name: str | None = None
    day: int | None = Field(default=None, ge=1, le=31)
    month: int | None = Field(default=None, ge=1, le=12)
    year: int | None = Field(default=None, ge=1800, le=2399)
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)
    birth_place: str | None = None


class BirthProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    name: str
    day: int
    month: int
    year: int
    hour: int
    minute: int
    birth_place: str
    created_at: datetime
