from fastapi import Body, HTTPException
from fastapi.routing import APIRouter

from app.services.coord_utils import get_coordinates
from app.services.kundali_chart import planets_calculation
from app.models import APIBirthDetails, BirthChart, KundaliChart

router = APIRouter()


@router.post("/kundali")
def get_my_kundali(
    birth_details: APIBirthDetails = Body(...),
) -> KundaliChart:
    coords = get_coordinates(birth_details.birth_place)
    if not coords:
        raise HTTPException(status_code=400, detail="Invalid birth place name")
    
    birth_chart = BirthChart(
        day=birth_details.day,
        month=birth_details.month,
        year=birth_details.year,
        hour=birth_details.hour,
        minute=birth_details.minute,
        second=birth_details.second,
        latitude=coords["latitude"],
        longitude=coords["longitude"],
    )
    
    kundali_chart = planets_calculation(birth_chart)
    return kundali_chart
