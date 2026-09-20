from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, Field, model_serializer

class APIBirthDetails(BaseModel):
    day: int
    month: int
    year: int = Field(..., ge=1800, le=2399)
    hour: int
    minute: int
    second: int
    birth_place: str = "Ahmedabad, Gujarat, India"

class BirthChart(BaseModel):
    day: int
    month: int
    year: int
    hour: int
    minute: int
    second: int
    timezone: float = 5.5 # GMT + 5:30
    latitude: float = 23.03 # ahmedabad, gujarat
    longitude: float = 72.62 # ahmedabad, gujarat

class DashaPeriod(BaseModel):
    lord: str
    start: datetime
    end: datetime
    duration_years: float
    duration_days: float


class MahadashaWithAntardashas(BaseModel):
    mahadasha: DashaPeriod
    antardashas: List[DashaPeriod]


class VimshottariChart(BaseModel):
    mahadashas: List[MahadashaWithAntardashas]


class PlanetData(BaseModel):
    name: str
    position: float  # Internal use only - not exposed in API responses
    house: int
    zodiac: str
    deviation: float  # Internal use only - not exposed in API responses
    retrograde: bool
    
    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """Exclude position and deviation from serialization."""
        return {
            "name": self.name,
            "house": self.house,
            "zodiac": self.zodiac,
            "retrograde": self.retrograde
        }

class KundaliChart(BaseModel):
    ascendant: float
    ascendant_sign: str
    planets: Dict[str, PlanetData]
    moon_zodiac: str
    moon_deviate: float  # Internal use only - not exposed in API responses
    nakshatra: str

    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """Exclude moon_deviate from serialization."""
        return {
            "ascendant": self.ascendant,
            "ascendant_sign": self.ascendant_sign,
            "planets": {k: planet.model_dump() for k, planet in self.planets.items()},
            "moon_zodiac": self.moon_zodiac,
            "nakshatra": self.nakshatra,
        }

class AshtakootaProfile(BaseModel):
    moon_zodiac: str
    nakshatra: str
    varna: str
    vashya: str
    tara: int
    yoni: str
    graha_maitri: str
    gana: str
    bhakoota: str
    nadi: str

class AshtakootaMatchScore(BaseModel):
    varna: float = 0
    vashya: float = 0
    tara: float = 0
    yoni: float = 0
    graha_maitri: float = 0
    gana: float = 0
    bhakoota: float = 0
    nadi: float = 0
    total: float = 0


class VargaPlanetData(BaseModel):
    name: str
    zodiac: str
    house: int


class VargaChart(BaseModel):
    ascendant_sign: str
    planets: Dict[str, VargaPlanetData]


class MangalDoshaResult(BaseModel):
    has_dosha: bool
    mars_house: int
    severity: str | None          # "high" | "medium" | "mild" | None
    cancelled: bool
    cancellation_reasons: list[str]
    mars_sign: str


class MangalDoshaCompatibility(BaseModel):
    user: MangalDoshaResult
    partner: MangalDoshaResult
    pairing: str                  # "none" | "balanced" | "asymmetric"
