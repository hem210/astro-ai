import swisseph as swe
from datetime import datetime, timedelta
from app.models import BirthChart, KundaliChart, PlanetData

# Set the ayanamsa to Lahiri (sidereal)
swe.set_sid_mode(swe.SIDM_LAHIRI)

# Function to calculate Julian Day
def julian_day(year, month, day, hour=0, minute=0, second=0, tz_offset=5.5):
    dt = datetime(year, month, day, hour, minute, second) - timedelta(hours=tz_offset)
    jd = swe.julday(dt.year, dt.month, dt.day, (hour + minute/60 + second/3600), swe.GREG_CAL)
    return jd

# Function to calculate planetary positions
def calculate_planetary_positions(jd, latitude, longitude):

    # Set the observer's location (topocentric)
    swe.set_topo(longitude, latitude, 53)

    # List of planets including Rahu and Ketu (mean node for Rahu)
    planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'rahu', 'ketu']
    positions = {}
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    # flags = swe.FLG_SIDEREAL | swe.FLG_TOPOCTR | swe.FLG_SWIEPH
    # print(flags)
    for planet in planets:
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

    return positions

# Function to calculate the Ascendant (Lagna)
def calculate_ascendant(jd, latitude, longitude):
    # print("calculating ascendant")
    flags = swe.FLG_SIDEREAL
    # print(swe.houses_ex(jd, latitude, longitude, b'W', flags))
    asc = swe.houses_ex(jd, latitude, longitude, b'W', swe.FLG_SIDEREAL)[1][0]  # A is for Placidus system, W is for Whole system
    return asc
    # return 24.2

# Function to determine which house each planet is in
def determine_houses(ascendant, positions):
    houses = {}
    
    for planet, pos in positions.items():
        # Calculate the relative position of the planet from the ascendant
        # relative_pos = (pos - ascendant) % 360
        
        # Determine the house based on relative position (each house is 30 degrees)
        house = int(pos / 30) + 1
        if pos>30:
            deviate = pos - (house-1)*30
        else:
            deviate = pos
        # {planet: {"house": house, "deviate": deviate}}
        houses[planet] = {"house": house, "deviate": deviate}
    return houses

def get_zodiac_sign(longitude):
    # List of zodiac signs in order
    zodiac_signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    
    # Each zodiac sign covers 30 degrees, so divide the longitude by 30 to find the sign
    sign_index = int(longitude // 30)  # Integer division to determine the sign
    sign_degrees = longitude % 30      # Remainder gives the degrees within the sign
    
    return zodiac_signs[sign_index]

# Function to calculate Nakshatra
def calculate_nakshatra(jd):
    # Moon position
    flags = swe.FLG_SIDEREAL | swe.FLG_TOPOCTR | swe.FLG_SWIEPH
    moon_pos = swe.calc_ut(jd, swe.MOON, flags)[0][0]
    # Nakshatra calculation
    nakshatra_index = int(moon_pos / 13.33333)  # 360 degrees / 27 Nakshatras
    nakshatras = [
        'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 
        'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
        'Hasta', 'Chitra', 'Swati', 'Visakha', 'Anuradha', 'Jyeshtha', 
        'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 
        'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
    ]
    nakshatra = nakshatras[nakshatra_index % 27]
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

    positions = calculate_planetary_positions(jd, birth_chart.latitude, birth_chart.longitude)
    ascendant = calculate_ascendant(jd, birth_chart.latitude, birth_chart.longitude)
    houses = determine_houses(ascendant, positions)
    nakshatra = calculate_nakshatra(jd)

    planets_data = {}

    for planet, pos in positions.items():
        zodiac = get_zodiac_sign(pos)
        house = houses[planet]["house"]
        deviation = houses[planet]["deviate"]
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