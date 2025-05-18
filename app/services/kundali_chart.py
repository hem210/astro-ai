import swisseph as swe
from datetime import datetime, timedelta
from app.models import BirthChart, KundaliChart, PlanetData
from app.config import ZODIACS, PLANETS, NAKSHATRAS

# Set the ayanamsa to Lahiri (sidereal)
swe.set_sid_mode(swe.SIDM_LAHIRI)

# Function to calculate Julian Day
def julian_day(year, month, day, hour=0, minute=0, second=0, tz_offset=5.5):
    swe.set_ephe_path('./eph')
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    dt = datetime(year, month, day, hour, minute, second) - timedelta(hours=tz_offset)
    jd = swe.julday(dt.year, dt.month, dt.day, (dt.hour + dt.minute/60 + dt.second/3600), swe.GREG_CAL)
    swe.close()
    return jd

def calculate_ascendant(jd, latitude, longitude):
    swe.set_ephe_path('./eph')
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL
    cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b'W', flags)  # A is for Placidus system, W is for Whole system
    swe.close()
    return ascmc[0]

def calculate_planetary_positions(jd):
    swe.set_ephe_path('./eph')
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # List of planets including Rahu and Ketu (mean node for Rahu)
    positions = {}
    flags = swe.FLG_SIDEREAL
    for planet in PLANETS:
        if planet == 'rahu':
            # Calculate Rahu (mean node)
            node_pos = swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0]
            positions['rahu'] = node_pos
            # Calculate Ketu (180 degrees opposite to Rahu)
            positions['ketu'] = (node_pos + 180) % 360
        elif planet == 'ketu':
            pass
        else:
            planet_id = getattr(swe, planet.upper())
            position = swe.calc_ut(jd, planet_id, flags)[0][0]
            positions[planet] = position
    
    swe.close()

    return positions

def determine_house(ascendant, pos):
    asc_house = int(ascendant / 30) + 1
    pl_sign = int(pos/30) + 1
    pl_house = (pl_sign - asc_house + 12) % 12 + 1
    return {"house": pl_house, "deviate": pos % 30}

def determine_zodiac(pos):
    return ZODIACS[int(pos/30) + 1]["name"]

# Function to calculate Nakshatra
def calculate_nakshatra(jd):
    swe.set_ephe_path('./eph')
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL

    moon_pos = swe.calc_ut(jd, swe.MOON, flags)[0][0]
    # Nakshatra calculation
    nakshatra_index = int(moon_pos / 13.33333)  # 360 degrees / 27 Nakshatras
    nakshatra = NAKSHATRAS[(nakshatra_index % 27) + 1]["name"]

    swe.close()
    return nakshatra

def planets_calculation(birth_chart: BirthChart) -> KundaliChart:
    jd = julian_day(
        birth_chart.year,
        birth_chart.month,
        birth_chart.day,
        birth_chart.hour,
        birth_chart.minute,
        birth_chart.second,
        birth_chart.timezone
    )

    positions = calculate_planetary_positions(jd)
    ascendant = calculate_ascendant(jd, birth_chart.latitude, birth_chart.longitude)
    nakshatra = calculate_nakshatra(jd)

    planets_data = {}

    for planet, pos in positions.items():
        house_obj = determine_house(ascendant, pos)
        house = house_obj["house"]
        deviation = house_obj["deviate"]
        zodiac = determine_zodiac(pos)
        planets_data[planet] = PlanetData(name=planet, position=pos, house=house, zodiac=zodiac, deviation=deviation)

    return KundaliChart(
        ascendant=ascendant,
        nakshatra=nakshatra,
        planets=planets_data,
        moon_zodiac=planets_data['moon'].zodiac,
        moon_deviate=planets_data['moon'].deviation
    )


if __name__ == "__main__":
    birth_chart = BirthChart(
        year = 2025,
        month = 5,
        day = 13,
        hour = 8,
        minute = 41,
        second = 0,
        timezone = 5.5, # GMT+5:30
        latitude = 23.03,  # ahmedabad
        longitude = 72.62,
    )
    

    details = planets_calculation(birth_chart=birth_chart)
    print(details)
    swe.close()
    
# def calculate_ascendant(jd, latitude, longitude):
#     swe.set_sidm
#     flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
#     print(swe.houses_ex(jd, latitude, longitude, b'W', flags))
#     cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b'W', swe.FLG_SIDEREAL)  # A is for Placidus system, W is for Whole system

#     return ascmc[0] # Acendant is the first element of the ascmc array