import swisseph as swe
from datetime import datetime, timedelta
from app.models import BirthChart, KundaliChart, VargaChart, VargaPlanetData, PlanetData
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
    retrograde_status = {}
    flags = swe.FLG_SIDEREAL
    for planet in PLANETS:
        if planet == 'rahu':
            # Calculate Rahu (mean node)
            node_pos = swe.calc_ut(jd, swe.MEAN_NODE, flags)[0][0]
            positions['rahu'] = node_pos
            # Rahu is always retrograde (moves backwards)
            retrograde_status['rahu'] = True
            
            # Calculate Ketu (180 degrees opposite to Rahu)
            positions['ketu'] = (node_pos + 180) % 360
            # Ketu is always retrograde (opposite of Rahu, always moves backwards)
            retrograde_status['ketu'] = True
        elif planet == 'ketu':
            pass
        else:
            planet_id = getattr(swe, planet.upper())
            planet_result = swe.calc_ut(jd, planet_id, flags)
            position = planet_result[0][0]
            speed = planet_result[0][3]  # Speed in longitude (degrees per day)
            positions[planet] = position
            # Planet is retrograde if speed is negative
            retrograde_status[planet] = speed < 0
    
    swe.close()

    return positions, retrograde_status

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

    positions, retrograde_status = calculate_planetary_positions(jd)
    ascendant = calculate_ascendant(jd, birth_chart.latitude, birth_chart.longitude)
    ascendant_sign = determine_zodiac(ascendant)
    nakshatra = calculate_nakshatra(jd)

    planets_data = {}

    for planet, pos in positions.items():
        house_obj = determine_house(ascendant, pos)
        house = house_obj["house"]
        deviation = house_obj["deviate"]
        zodiac = determine_zodiac(pos)
        retrograde = retrograde_status.get(planet, False)
        planets_data[planet] = PlanetData(
            name=planet, 
            position=pos, 
            house=house, 
            zodiac=zodiac, 
            deviation=deviation,
            retrograde=retrograde
        )

    return KundaliChart(
        ascendant=ascendant,
        ascendant_sign=ascendant_sign,
        nakshatra=nakshatra,
        planets=planets_data,
        moon_zodiac=planets_data['moon'].zodiac,
        moon_deviate=planets_data['moon'].deviation,
    )


# Navamsa starting sign per D1 sign
# Fire (1,5,9)→Aries(1)  Earth (2,6,10)→Capricorn(10)
# Air  (3,7,11)→Libra(7) Water (4,8,12)→Cancer(4)
_NAVAMSA_START = {
    1: 1, 2: 10, 3: 7,  4: 4,
    5: 1, 6: 10, 7: 7,  8: 4,
    9: 1, 10: 10, 11: 7, 12: 4,
}


def _d9_sign_num(longitude: float) -> int:
    d1_sign = int(longitude / 30) + 1
    pada = int((longitude % 30) / (30 / 9))
    return (_NAVAMSA_START[d1_sign] - 1 + pada) % 12 + 1


def calculate_navamsa(kundali: KundaliChart) -> VargaChart:
    asc_sign_num = _d9_sign_num(kundali.ascendant)

    planets: dict[str, VargaPlanetData] = {}
    for name, planet in kundali.planets.items():
        sign_num = _d9_sign_num(planet.position)
        house = (sign_num - asc_sign_num) % 12 + 1
        planets[name] = VargaPlanetData(
            name=name,
            zodiac=ZODIACS[sign_num]["name"],
            house=house,
        )

    return VargaChart(
        ascendant_sign=ZODIACS[asc_sign_num]["name"],
        planets=planets,
    )


# D10 starting sign per D1 sign
# Odd sign  → sign itself
# Even sign → 9th sign from it: (sign + 7) % 12 + 1
_DASHAMSHA_START = {
    1:  1,   2: 10,  3:  3,  4: 12,
    5:  5,   6:  2,  7:  7,  8:  4,
    9:  9,  10:  6, 11: 11, 12:  8,
}


def _d10_sign_num(longitude: float) -> int:
    d1_sign = int(longitude / 30) + 1
    pada = int((longitude % 30) / 3)        # 0–9, each pada = 3°
    return (_DASHAMSHA_START[d1_sign] - 1 + pada) % 12 + 1


def calculate_dashamsha(kundali: KundaliChart) -> VargaChart:
    asc_sign_num = _d10_sign_num(kundali.ascendant)

    planets: dict[str, VargaPlanetData] = {}
    for name, planet in kundali.planets.items():
        sign_num = _d10_sign_num(planet.position)
        house = (sign_num - asc_sign_num) % 12 + 1
        planets[name] = VargaPlanetData(
            name=name,
            zodiac=ZODIACS[sign_num]["name"],
            house=house,
        )

    return VargaChart(
        ascendant_sign=ZODIACS[asc_sign_num]["name"],
        planets=planets,
    )


def _d12_sign_num(longitude: float) -> int:
    d1_sign = int(longitude / 30) + 1
    pada = int((longitude % 30) / 2.5)     # 0–11, each pada = 2°30'
    return (d1_sign - 1 + pada) % 12 + 1


def calculate_dvadashamsha(kundali: KundaliChart) -> VargaChart:
    asc_sign_num = _d12_sign_num(kundali.ascendant)

    planets: dict[str, VargaPlanetData] = {}
    for name, planet in kundali.planets.items():
        sign_num = _d12_sign_num(planet.position)
        house = (sign_num - asc_sign_num) % 12 + 1
        planets[name] = VargaPlanetData(
            name=name,
            zodiac=ZODIACS[sign_num]["name"],
            house=house,
        )

    return VargaChart(
        ascendant_sign=ZODIACS[asc_sign_num]["name"],
        planets=planets,
    )


if __name__ == "__main__":
    birth_chart = BirthChart(
        year = 1972,
        month = 4,
        day = 11,
        hour = 11,
        minute = 0,
        second = 0,
        timezone = 5.5, # GMT+5:30
        latitude = 21.64,  # ahmedabad
        longitude = 69.61,
    )
    

    details = planets_calculation(birth_chart=birth_chart)
    print(details.model_dump_json())
    swe.close()
    
# def calculate_ascendant(jd, latitude, longitude):
#     swe.set_sidm
#     flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
#     print(swe.houses_ex(jd, latitude, longitude, b'W', flags))
#     cusps, ascmc = swe.houses_ex(jd, latitude, longitude, b'W', swe.FLG_SIDEREAL)  # A is for Placidus system, W is for Whole system

#     return ascmc[0] # Acendant is the first element of the ascmc array