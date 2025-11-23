from pydantic import BaseModel, Field
from typing import Dict

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

class PlanetData(BaseModel):
    name: str
    position: float
    house: int
    zodiac: str
    deviation: float
    retrograde: bool

class KundaliChart(BaseModel):
    ascendant: float
    ascendant_sign: str
    planets: Dict[str, PlanetData]
    moon_zodiac: str
    moon_deviate: float
    nakshatra: str

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
