"""
Vimshottari Dasha Tool

Returns the mahadasha and antardasha periods active within a given date range,
computed from the birth chart's Moon position. Use this tool when a question
has a time dimension — "right now", "next year", "in 2028", etc.
"""

from datetime import datetime
from typing import Any, Dict, List

from langchain_core.tools import tool

from app.models import BirthChart
from app.services.coord_utils import get_coordinates
from app.services.kundali_chart import (
    calculate_planetary_positions,
    julian_day,
)
from app.services.vimshottari import compute_vimshottari, find_dashas_in_range


@tool
def get_vimshottari_dasha(
    day: int,
    month: int,
    year: int,
    hour: int,
    minute: int,
    start_date: str,
    end_date: str,
    second: int = 0,
    birth_place: str = "Ahmedabad, Gujarat, India",
) -> List[Dict[str, Any]]:
    """
    Return Vimshottari dasha periods active within a date range for a given birth chart.

    Use this tool when the user's question has a time dimension — explicit or implied.
    Examples of when to call it:
      - "What dasha am I in?" → start_date = today, end_date = today
      - "What's my dasha next year?" → start_date = today, end_date = one year from today
      - "What was happening astrologically in 2020?" → start_date = 2020-01-01, end_date = 2020-12-31
      - "How are the next 3 years for my career?" → start_date = today, end_date = three years from today
      - "Is this a good time to..." → start_date = today, end_date = today

    The tool returns every mahadasha/antardasha pair that overlaps the given range,
    so a multi-year range may return several periods if transitions fall within it.

    Args:
        day: Day of birth (1-31)
        month: Month of birth (1-12)
        year: Year of birth (1800-2399)
        hour: Hour of birth in 24h format (0-23)
        minute: Minute of birth (0-59)
        start_date: Range start as "YYYY-MM-DD"
        end_date: Range end as "YYYY-MM-DD" (same as start_date for a single-day query)
        second: Second of birth (0-59), defaults to 0
        birth_place: Birth place name, defaults to "Ahmedabad, Gujarat, India"

    Returns:
        List of dicts, each with:
        - mahadasha: { lord, start, end, duration_years }
        - antardasha: { lord, start, end, duration_years }

        Periods are in chronological order. An empty list means no dasha data
        is available for the given range (e.g., range is beyond the 120-year cycle).

    Example:
        get_vimshottari_dasha(
            day=15, month=6, year=1990,
            hour=10, minute=30,
            start_date="2026-01-01",
            end_date="2026-12-31",
            birth_place="Mumbai, Maharashtra, India"
        )
    """
    # Resolve coordinates
    coords = get_coordinates(birth_place)
    if not coords:
        coords = {"latitude": 23.03, "longitude": 72.62}

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

    # Compute birth Julian date and Moon longitude
    birth_jd = julian_day(
        birth_chart.year,
        birth_chart.month,
        birth_chart.day,
        birth_chart.hour,
        birth_chart.minute,
        birth_chart.second,
        birth_chart.timezone,
    )
    positions, _ = calculate_planetary_positions(birth_jd)
    moon_longitude = positions["moon"]

    # Build full Vimshottari chart
    vimshottari_chart = compute_vimshottari(birth_chart, birth_jd, moon_longitude)

    # Parse the requested range
    # end_date is set to 23:59:59 so a single-day query (start == end) still matches
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
        hour=23, minute=59, second=59
    )

    return find_dashas_in_range(vimshottari_chart, start_dt, end_dt)
