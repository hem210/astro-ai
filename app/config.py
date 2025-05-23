import os
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

ZODIACS = {
    1: {"id": 1,
    "name": "Aries"},
    2: {"id": 2,
    "name": "Taurus"},
    3: {"id": 3,
    "name": "Gemini"},
    4: {"id": 4,
    "name": "Cancer"},
    5: {"id": 5,
    "name": "Leo"},
    6: {"id": 6,
    "name": "Virgo"},
    7: {"id": 7,
    "name": "Libra"},
    8: {"id": 8,
    "name": "Scorpio"},
    9: {"id": 9,
    "name": "Sagittarius"},
    10: {"id": 10,
    "name": "Capricorn"},
    11: {"id": 11,
    "name": "Aquarius"},
    12: {"id": 12,
    "name": "Pisces"}
}

NAKSHATRAS = {
    1: {"id": 1,
     "name": "Ashwini"},
    2: {"id": 2,
     "name": "Bharani"},
    3: {"id": 3,
     "name": "Krittika"},
    4: {"id": 4,
     "name": "Rohini"},
    5: {"id": 5,
     "name": "Mrigashira"},
    6: {"id": 6,
     "name": "Ardra"},
    7: {"id": 7,
     "name": "Punarvasu"},
    8: {"id": 8,
     "name": "Pushya"},
    9: {"id": 9,
     "name": "Ashlesha"},
    10: {"id": 10,
     "name": "Magha"},
    11: {"id": 11,
     "name": "Purva Phalguni"},
    12: {"id": 12,
     "name": "Uttara Phalguni"},
    13: {"id": 13,
     "name": "Hasta"},
    14: {"id": 14,
     "name": "Chitra"},
    15: {"id": 15,
     "name": "Swati"},
    16: {"id": 16,
     "name": "Visakha"},
    17: {"id": 17,
     "name": "Anuradha"},
    18: {"id": 18,
     "name": "Jyeshtha"},
    19: {"id": 19,
     "name": "Mula"},
    20: {"id": 20,
     "name": "Purva Ashadha"},
    21: {"id": 21,
     "name": "Uttara Ashadha"},
    22: {"id": 22,
     "name": "Shravana"},
    23: {"id": 23,
     "name": "Dhanishta"},
    24: {"id": 24,
     "name": "Shatabhisha"},
    25: {"id": 25,
     "name": "Purva Bhadrapada"},
    26: {"id": 26,
     "name": "Uttara Bhadrapada"},
    27: {"id": 27,
     "name": "Revati"}
}

PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "rahu", "ketu"]
