import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompatibilityScoreResponse(BaseModel):
    varna: float
    vashya: float
    tara: float
    yoni: float
    graha_maitri: float
    gana: float
    bhakoota: float
    nadi: float
    total: float


class CompatibilityMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class MangalDoshaResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    has_dosha: bool
    mars_house: int
    severity: str | None
    cancelled: bool
    cancellation_reasons: list[str]
    mars_sign: str


class MangalDoshaCompatibilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user: MangalDoshaResultResponse
    partner: MangalDoshaResultResponse
    pairing: str


class CompatibilityStateResponse(BaseModel):
    score: CompatibilityScoreResponse | None
    conversation_id: uuid.UUID | None
    messages: list[CompatibilityMessageResponse]
    mangal_dosha: MangalDoshaCompatibilityResponse | None


class CompatibilityChatRequest(BaseModel):
    message: str
