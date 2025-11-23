"""
Kundali Chart Generation Tool

This tool generates a kundali (natal chart) based on birth details.
It's designed to be used with LangGraph agents.
"""

from langchain_core.tools import tool
from app.models import BirthChart
from app.services.kundali_chart import planets_calculation
from app.services.coord_utils import get_coordinates
from typing import Dict, Any


@tool
def generate_kundali_chart(
    day: int,
    month: int,
    year: int,
    hour: int,
    minute: int,
    second: int = 0,
    birth_place: str = "Ahmedabad, Gujarat, India"
) -> Dict[str, Any]:
    """
    Generate a kundali (natal chart) based on birth details.
    
    This tool calculates planetary positions, houses, signs, ascendant, and nakshatra
    for a given birth date, time, and place.
    
    Args:
        day: Day of birth (1-31)
        month: Month of birth (1-12)
        year: Year of birth (1800-2399)
        hour: Hour of birth (0-23)
        minute: Minute of birth (0-59)
        second: Second of birth (0-59), defaults to 0
        birth_place: Birth place name (e.g., "Ahmedabad, Gujarat, India"), defaults to "Ahmedabad, Gujarat, India"
    
    Returns:
        Dictionary containing:
        - ascendant: Ascendant position in degrees
        - ascendant_sign: Zodiac sign of ascendant
        - nakshatra: Moon's nakshatra
        - planets: Dictionary of planetary positions with keys:
          - name: Planet name
          - position: Position in degrees
          - house: House number (1-12)
          - zodiac: Zodiac sign
          - deviation: Deviation within sign
          - retrograde: Whether planet is retrograde
        - moon_zodiac: Moon's zodiac sign
        - moon_deviate: Moon's deviation within sign
    
    Example:
        generate_kundali_chart(
            day=15,
            month=6,
            year=1990,
            hour=10,
            minute=30,
            birth_place="Mumbai, Maharashtra, India"
        )
    """
    # Get coordinates for birth place
    coords = get_coordinates(birth_place)
    if not coords:
        # Use default coordinates if geocoding fails
        coords = {"latitude": 23.03, "longitude": 72.62}
    
    # Create birth chart
    birth_chart = BirthChart(
        day=day,
        month=month,
        year=year,
        hour=hour,
        minute=minute,
        second=second,
        latitude=coords.get("latitude", 23.03),
        longitude=coords.get("longitude", 72.62),
    )
    
    # Calculate kundali
    kundali_chart = planets_calculation(birth_chart)
    
    # Convert to dictionary for tool response
    result = {
        "ascendant": kundali_chart.ascendant,
        "ascendant_sign": kundali_chart.ascendant_sign,
        "nakshatra": kundali_chart.nakshatra,
        "planets": {},
        "moon_zodiac": kundali_chart.moon_zodiac,
        "moon_deviate": kundali_chart.moon_deviate,
    }
    
    # Convert planet data to dictionaries
    for planet_name, planet_data in kundali_chart.planets.items():
        result["planets"][planet_name] = {
            "name": planet_data.name,
            "position": planet_data.position,
            "house": planet_data.house,
            "zodiac": planet_data.zodiac,
            "deviation": planet_data.deviation,
            "retrograde": planet_data.retrograde,
        }
    
    return result

