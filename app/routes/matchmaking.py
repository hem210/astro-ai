from fastapi import Body
from fastapi.routing import APIRouter
from app.services.ashtakoota_services.generate_profile import generate_ashtakoota_profile
from app.services.compatibility import compute_score_from_birth_details
from app.services.coord_utils import get_coordinates
from app.services.kundali_chart import planets_calculation
from app.services.explanation_pipeline import ashtakoota_explanation_pipeline
from app.models import APIBirthDetails, AshtakootaMatchScore, BirthChart

router = APIRouter()


@router.post("/ashtakoota-score")
async def ashtakoota_score(
    groom_birth_details: APIBirthDetails = Body(...),
    bride_birth_details: APIBirthDetails = Body(...)
) -> AshtakootaMatchScore:
    return compute_score_from_birth_details(
        groom_birth_details.day, groom_birth_details.month, groom_birth_details.year,
        groom_birth_details.hour, groom_birth_details.minute, groom_birth_details.birth_place,
        bride_birth_details.day, bride_birth_details.month, bride_birth_details.year,
        bride_birth_details.hour, bride_birth_details.minute, bride_birth_details.birth_place,
    )


@router.post("/ashtakoota-score-explain")
async def ashtakoota_score_explain(
    groom_birth_details: APIBirthDetails = Body(...),
    bride_birth_details: APIBirthDetails = Body(...)
):
    score = compute_score_from_birth_details(
        groom_birth_details.day, groom_birth_details.month, groom_birth_details.year,
        groom_birth_details.hour, groom_birth_details.minute, groom_birth_details.birth_place,
        bride_birth_details.day, bride_birth_details.month, bride_birth_details.year,
        bride_birth_details.hour, bride_birth_details.minute, bride_birth_details.birth_place,
    )

    def _chart(d: APIBirthDetails):
        coords = get_coordinates(d.birth_place) or {"latitude": 23.03, "longitude": 72.62}
        return planets_calculation(BirthChart(
            day=d.day, month=d.month, year=d.year,
            hour=d.hour, minute=d.minute, second=d.second,
            latitude=coords["latitude"], longitude=coords["longitude"],
        ))

    groom_chart = _chart(groom_birth_details)
    bride_chart = _chart(bride_birth_details)
    groom_profile = generate_ashtakoota_profile(
        groom_chart.planets["moon"].zodiac, groom_chart.planets["moon"].deviation, groom_chart.nakshatra
    )
    bride_profile = generate_ashtakoota_profile(
        bride_chart.planets["moon"].zodiac, bride_chart.planets["moon"].deviation, bride_chart.nakshatra
    )

    response = await ashtakoota_explanation_pipeline(score, groom_profile, bride_profile)
    return {"ashtakoota_score_explain": response}
