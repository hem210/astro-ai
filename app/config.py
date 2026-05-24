import os
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

ZODIACS = {
    1:  {"id": 1,  "name": "Aries",       "lord": "mars"},
    2:  {"id": 2,  "name": "Taurus",      "lord": "venus"},
    3:  {"id": 3,  "name": "Gemini",      "lord": "mercury"},
    4:  {"id": 4,  "name": "Cancer",      "lord": "moon"},
    5:  {"id": 5,  "name": "Leo",         "lord": "sun"},
    6:  {"id": 6,  "name": "Virgo",       "lord": "mercury"},
    7:  {"id": 7,  "name": "Libra",       "lord": "venus"},
    8:  {"id": 8,  "name": "Scorpio",     "lord": "mars"},
    9:  {"id": 9,  "name": "Sagittarius", "lord": "jupiter"},
    10: {"id": 10, "name": "Capricorn",   "lord": "saturn"},
    11: {"id": 11, "name": "Aquarius",    "lord": "saturn"},
    12: {"id": 12, "name": "Pisces",      "lord": "jupiter"},
}

NAKSHATRAS = {
    1: {"id": 1, "name": "Ashwini", "lord": "ketu"},
    2: {"id": 2, "name": "Bharani", "lord": "venus"},
    3: {"id": 3, "name": "Krittika", "lord": "sun"},
    4: {"id": 4, "name": "Rohini", "lord": "moon"},
    5: {"id": 5, "name": "Mrigashira", "lord": "mars"},
    6: {"id": 6, "name": "Ardra", "lord": "rahu"},
    7: {"id": 7, "name": "Punarvasu", "lord": "jupiter"},
    8: {"id": 8, "name": "Pushya", "lord": "saturn"},
    9: {"id": 9, "name": "Ashlesha", "lord": "mercury"},
    10: {"id": 10, "name": "Magha", "lord": "ketu"},
    11: {"id": 11, "name": "Purva Phalguni", "lord": "venus"},
    12: {"id": 12, "name": "Uttara Phalguni", "lord": "sun"},
    13: {"id": 13, "name": "Hasta", "lord": "moon"},
    14: {"id": 14, "name": "Chitra", "lord": "mars"},
    15: {"id": 15, "name": "Swati", "lord": "rahu"},
    16: {"id": 16, "name": "Visakha", "lord": "jupiter"},
    17: {"id": 17, "name": "Anuradha", "lord": "saturn"},
    18: {"id": 18, "name": "Jyeshtha", "lord": "mercury"},
    19: {"id": 19, "name": "Mula", "lord": "ketu"},
    20: {"id": 20, "name": "Purva Ashadha", "lord": "venus"},
    21: {"id": 21, "name": "Uttara Ashadha", "lord": "sun"},
    22: {"id": 22, "name": "Shravana", "lord": "moon"},
    23: {"id": 23, "name": "Dhanishta", "lord": "mars"},
    24: {"id": 24, "name": "Shatabhisha", "lord": "rahu"},
    25: {"id": 25, "name": "Purva Bhadrapada", "lord": "jupiter"},
    26: {"id": 26, "name": "Uttara Bhadrapada", "lord": "saturn"},
    27: {"id": 27, "name": "Revati", "lord": "mercury"},
}

VIMSHOTTARI_CHRONOLOGY = (
    "ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury",
)

VIMSHOTTARI_YEARS = {
    "ketu": 7.0,
    "venus": 20.0,
    "sun": 6.0,
    "moon": 10.0,
    "mars": 7.0,
    "rahu": 18.0,
    "jupiter": 16.0,
    "saturn": 19.0,
    "mercury": 17.0,
}

PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "rahu", "ketu"]
