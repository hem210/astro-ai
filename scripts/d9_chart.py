"""
Standalone D9 (Navamsa) chart calculator.

Usage:
    python scripts/d9_chart.py

Edit the birth_details dict at the bottom to match the chart you want to verify.
The D1 positions are computed using the same swisseph + Lahiri ayanamsa setup
as the main app, then the D9 signs are derived from those positions.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import swisseph as swe
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

SIGN_NAMES = {
    1: "Aries",
    2: "Taurus",
    3: "Gemini",
    4: "Cancer",
    5: "Leo",
    6: "Virgo",
    7: "Libra",
    8: "Scorpio",
    9: "Sagittarius",
    10: "Capricorn",
    11: "Aquarius",
    12: "Pisces",
}

# Navamsa starting sign for each D1 sign
# Fire (1,5,9) → start from Aries (1)
# Earth (2,6,10) → start from Capricorn (10)
# Air (3,7,11) → start from Libra (7)
# Water (4,8,12) → start from Cancer (4)
NAVAMSA_START = {
    1: 1,   # Aries   → Aries
    2: 10,  # Taurus  → Capricorn
    3: 7,   # Gemini  → Libra
    4: 4,   # Cancer  → Cancer
    5: 1,   # Leo     → Aries
    6: 10,  # Virgo   → Capricorn
    7: 7,   # Libra   → Libra
    8: 4,   # Scorpio → Cancer
    9: 1,   # Sag     → Aries
    10: 10, # Cap     → Capricorn
    11: 7,  # Aquarius→ Libra
    12: 4,  # Pisces  → Cancer
}

PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "rahu", "ketu"]

# ---------------------------------------------------------------------------
# D1 calculation (same as app/services/kundali_chart.py)
# ---------------------------------------------------------------------------

swe.set_sid_mode(swe.SIDM_LAHIRI)


def julian_day(year, month, day, hour, minute, second=0, tz_offset=5.5):
    swe.set_ephe_path('./eph')
    dt = datetime(year, month, day, hour, minute, second) - timedelta(hours=tz_offset)
    jd = swe.julday(dt.year, dt.month, dt.day,
                    dt.hour + dt.minute / 60 + dt.second / 3600,
                    swe.GREG_CAL)
    return jd


def get_d1_positions(jd):
    swe.set_ephe_path('./eph')
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL
    positions = {}

    for planet in PLANETS:
        if planet == 'rahu':
            pos = swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0]
            positions['rahu'] = pos
            positions['ketu'] = (pos + 180) % 360
        elif planet == 'ketu':
            pass
        else:
            planet_id = getattr(swe, planet.upper())
            pos = swe.calc_ut(jd, planet_id, flags)[0][0]
            positions[planet] = pos

    return positions


def get_ascendant(jd, latitude, longitude):
    swe.set_ephe_path('./eph')
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL
    cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b'W', flags)
    return ascmc[0]


# ---------------------------------------------------------------------------
# D9 calculation
# ---------------------------------------------------------------------------

def d9_sign(longitude: float) -> int:
    """Given an absolute sidereal longitude (0–360), return the D9 sign (1–12)."""
    d1_sign = int(longitude / 30) + 1          # 1–12
    degrees_in_sign = longitude % 30           # 0–30
    pada = int(degrees_in_sign / (30 / 9))     # 0–8  (each pada = 3°20')
    start = NAVAMSA_START[d1_sign]
    navamsa = (start - 1 + pada) % 12 + 1     # 1–12
    return navamsa


def calculate_d9(birth_details: dict):
    jd = julian_day(
        birth_details['year'],
        birth_details['month'],
        birth_details['day'],
        birth_details['hour'],
        birth_details['minute'],
        birth_details.get('second', 0),
        birth_details.get('tz_offset', 5.5),
    )

    d1_positions = get_d1_positions(jd)
    asc_d1 = get_ascendant(jd, birth_details['latitude'], birth_details['longitude'])

    print("=" * 55)
    print("  D1 (Rasi) chart positions")
    print("=" * 55)
    print(f"  {'Planet':<12} {'D1 Long':>10}  {'D1 Sign':<14}")
    print("-" * 55)
    for planet in PLANETS:
        lon = d1_positions[planet]
        sign = SIGN_NAMES[int(lon / 30) + 1]
        deg_in_sign = lon % 30
        print(f"  {planet:<12} {lon:>9.4f}°  {sign:<14}  ({deg_in_sign:.4f}° in sign)")
    asc_sign = SIGN_NAMES[int(asc_d1 / 30) + 1]
    print(f"  {'Ascendant':<12} {asc_d1:>9.4f}°  {asc_sign:<14}  ({asc_d1 % 30:.4f}° in sign)")

    print()
    print("=" * 55)
    print("  D9 (Navamsa) chart")
    print("=" * 55)
    print(f"  {'Planet':<12} {'D9 Sign':<14}")
    print("-" * 55)
    for planet in PLANETS:
        lon = d1_positions[planet]
        sign_num = d9_sign(lon)
        print(f"  {planet:<12} {SIGN_NAMES[sign_num]}")
    asc_d9_sign = d9_sign(asc_d1)
    print(f"  {'Ascendant':<12} {SIGN_NAMES[asc_d9_sign]}")

    swe.close()


# ---------------------------------------------------------------------------
# Edit this dict to match the birth chart you want to verify
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    birth_details = {
        'year': 2026,
        'month': 9,
        'day': 14,
        'hour': 13,
        'minute': 2,
        'second': 0,
        'tz_offset': 5.5,       # IST = UTC+5:30
        'latitude': 23.03,      # Ahmedabad
        'longitude': 72.62,
    }

    calculate_d9(birth_details)
