"""
Varga (Divisional) Chart Tool

Computes D9 (Navamsa), D10 (Dashamsha), or D12 (Dvadashamsha) for a given birth profile.
"""

from typing import Dict, Any

from langchain_core.tools import tool

from app.models import BirthChart
from app.services.coord_utils import get_coordinates
from app.services.kundali_chart import (
    planets_calculation,
    calculate_navamsa,
    calculate_dashamsha,
    calculate_dvadashamsha,
)

_CALCULATORS = {
    "d9":  calculate_navamsa,
    "d10": calculate_dashamsha,
    "d12": calculate_dvadashamsha,
}

_CHART_NAMES = {
    "d9":  "Navamsa",
    "d10": "Dashamsha",
    "d12": "Dvadashamsha",
}


@tool
def get_varga_chart(
    chart_type: str,
    day: int,
    month: int,
    year: int,
    hour: int,
    minute: int,
    second: int = 0,
    birth_place: str = "Ahmedabad, Gujarat, India",
) -> Dict[str, Any]:
    """
    Compute a Vedic divisional (varga) chart for a given birth profile.

    Use this tool when the question requires a divisional chart beyond D1:
      - chart_type="d9"  (Navamsa)     — marriage, spouse traits, relationship karma, spiritual life
      - chart_type="d10" (Dashamsha)   — career, profession, social status, professional achievements
      - chart_type="d12" (Dvadashamsha)— parents, father/mother influence, ancestral karma

    Args:
        chart_type: Which divisional chart to compute. One of: "d9", "d10", "d12"
        day: Day of birth (1-31)
        month: Month of birth (1-12)
        year: Year of birth
        hour: Hour of birth (0-23)
        minute: Minute of birth (0-59)
        second: Second of birth (0-59), defaults to 0
        birth_place: Birth place name, defaults to "Ahmedabad, Gujarat, India"

    Returns:
        Dictionary with:
        - chart_type: e.g. "d9"
        - chart_name: e.g. "Navamsa"
        - ascendant_sign: Ascendant sign in this divisional chart
        - planets: dict of planet → { zodiac, house } in this divisional chart
    """
    chart_type = chart_type.lower().strip()
    if chart_type not in _CALCULATORS:
        return {"error": f"Unsupported chart_type '{chart_type}'. Use one of: d9, d10, d12."}

    coords = get_coordinates(birth_place) or {"latitude": 23.03, "longitude": 72.62}

    kundali = planets_calculation(BirthChart(
        day=day, month=month, year=year,
        hour=hour, minute=minute, second=second,
        latitude=coords["latitude"],
        longitude=coords["longitude"],
    ))

    varga = _CALCULATORS[chart_type](kundali)

    return {
        "chart_type": chart_type,
        "chart_name": _CHART_NAMES[chart_type],
        "ascendant_sign": varga.ascendant_sign,
        "planets": {
            name: {"zodiac": p.zodiac, "house": p.house}
            for name, p in varga.planets.items()
        },
    }
