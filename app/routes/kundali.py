from fastapi import Body, HTTPException
from fastapi.routing import APIRouter

from app.services.coord_utils import get_coordinates
from app.services.kundali_chart import planets_calculation
from app.services.ashtakoota_services.generate_profile import generate_ashtakoota_profile
from app.services.match_finder import find_perfect_match
from app.models import APIBirthDetails, BirthChart, KundaliChart

router = APIRouter()


@router.post("/kundali")
def get_my_kundali(
    birth_details: APIBirthDetails = Body(...),
) -> KundaliChart:
    coords = get_coordinates(birth_details.birth_place)
    if not coords:
        print("Invalid birth place name, using default coordinates")
    
    birth_chart = BirthChart(
        day=birth_details.day,
        month=birth_details.month,
        year=birth_details.year,
        hour=birth_details.hour,
        minute=birth_details.minute,
        second=birth_details.second,
        latitude=coords.get("latitude", 23.03),
        longitude=coords.get("longitude", 72.62),
    )
    
    kundali_chart = planets_calculation(birth_chart)
    return kundali_chart

@router.post("/perfect-match")
def get_perfect_match(
    birth_details: APIBirthDetails = Body(...),
    type: str = Body(...),
):
    coords = get_coordinates(birth_details.birth_place)
    if not coords:
        print("Invalid birth place name, using default coordinates")
    
    birth_chart = BirthChart(
        day=birth_details.day,
        month=birth_details.month,
        year=birth_details.year,
        hour=birth_details.hour,
        minute=birth_details.minute,
        second=birth_details.second,
        latitude=coords.get("latitude", 23.03),
        longitude=coords.get("longitude", 72.62),
    )
    
    kundali_chart = planets_calculation(birth_chart)
    ashtakoota_profile = generate_ashtakoota_profile(
        kundali_chart.planets["moon"].zodiac, 
        kundali_chart.planets["moon"].deviation,
        kundali_chart.nakshatra
    )

    result = find_perfect_match(ashtakoota_profile, type)

    return {
        "result": result
    }
