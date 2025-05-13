from fastapi import Body, HTTPException
from fastapi.routing import APIRouter
from app.services.coord_utils import get_coordinates
from app.services.kundali_chart import planets_calculation
from app.services.ashtakoota_services.generate_profile import generate_ashtakoota_profile
from app.services.ashtakoota_services.calculate_score import calculate_ashtakoota
from app.services.explanation_pipeline import ashtakoota_explanation_pipeline
from app.models import APIBirthDetails, BirthChart, AshtakootaMatchScore

router = APIRouter()

@router.post("/ashtakoota-score")
async def ashtakoota_score(
    groom_birth_details: APIBirthDetails = Body(...),
    bride_birth_details: APIBirthDetails = Body(...)
) -> AshtakootaMatchScore:
    groom_coords = get_coordinates(groom_birth_details.birth_place)
    if not groom_coords:
        raise HTTPException(status_code=400, detail="Invalid birth place name of groom")
    
    groom_birth_chart = BirthChart(
        day=groom_birth_details.day,
        month=groom_birth_details.month,
        year=groom_birth_details.year,
        hour=groom_birth_details.hour,
        minute=groom_birth_details.minute,
        second=groom_birth_details.second,
        latitude=groom_coords["latitude"],
        longitude=groom_coords["longitude"],
    )

    groom_kundali_chart = planets_calculation(groom_birth_chart)

    bride_coords = get_coordinates(bride_birth_details.birth_place)
    if not bride_coords:
        raise HTTPException(status_code=400, detail="Invalid birth place name of bride")
    
    bride_birth_chart = BirthChart(
        day=bride_birth_details.day,
        month=bride_birth_details.month,
        year=bride_birth_details.year,
        hour=bride_birth_details.hour,
        minute=bride_birth_details.minute,
        second=bride_birth_details.second,
        latitude=bride_coords["latitude"],
        longitude=bride_coords["longitude"],
    )

    bride_kundali_chart = planets_calculation(bride_birth_chart)

    groom_ashtakoota_profile = generate_ashtakoota_profile(
        groom_kundali_chart.planets["moon"].zodiac, 
        groom_kundali_chart.planets["moon"].deviation,
        groom_kundali_chart.nakshatra
    )
    
    bride_ashtakoota_profile = generate_ashtakoota_profile(
        bride_kundali_chart.planets["moon"].zodiac, 
        bride_kundali_chart.planets["moon"].deviation,
        bride_kundali_chart.nakshatra
    )

    score = calculate_ashtakoota(groom_profile=groom_ashtakoota_profile,
                                bride_profile=bride_ashtakoota_profile)
    return score

@router.post("/ashtakoota-score-explain")
async def ashtakoota_score(
    groom_birth_details: APIBirthDetails = Body(...),
    bride_birth_details: APIBirthDetails = Body(...)
):
    groom_coords = get_coordinates(groom_birth_details.birth_place)
    if not groom_coords:
        raise HTTPException(status_code=400, detail="Invalid birth place name of groom")
    
    groom_birth_chart = BirthChart(
        day=groom_birth_details.day,
        month=groom_birth_details.month,
        year=groom_birth_details.year,
        hour=groom_birth_details.hour,
        minute=groom_birth_details.minute,
        second=groom_birth_details.second,
        latitude=groom_coords["latitude"],
        longitude=groom_coords["longitude"],
    )

    groom_kundali_chart = planets_calculation(groom_birth_chart)

    bride_coords = get_coordinates(bride_birth_details.birth_place)
    if not bride_coords:
        raise HTTPException(status_code=400, detail="Invalid birth place name of bride")
    
    bride_birth_chart = BirthChart(
        day=bride_birth_details.day,
        month=bride_birth_details.month,
        year=bride_birth_details.year,
        hour=bride_birth_details.hour,
        minute=bride_birth_details.minute,
        second=bride_birth_details.second,
        latitude=bride_coords["latitude"],
        longitude=bride_coords["longitude"],
    )

    bride_kundali_chart = planets_calculation(bride_birth_chart)

    groom_ashtakoota_profile = generate_ashtakoota_profile(
        groom_kundali_chart.planets["moon"].zodiac, 
        groom_kundali_chart.planets["moon"].deviation,
        groom_kundali_chart.nakshatra
    )
    
    bride_ashtakoota_profile = generate_ashtakoota_profile(
        bride_kundali_chart.planets["moon"].zodiac, 
        bride_kundali_chart.planets["moon"].deviation,
        bride_kundali_chart.nakshatra
    )

    score = calculate_ashtakoota(groom_profile=groom_ashtakoota_profile,
                                bride_profile=bride_ashtakoota_profile)
    
    response = await ashtakoota_explanation_pipeline(score, groom_ashtakoota_profile, bride_ashtakoota_profile)
    ashtakoota_score_explain = {"ashtakoota_score_explain": response}
    return ashtakoota_score_explain
