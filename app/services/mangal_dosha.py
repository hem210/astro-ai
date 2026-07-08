"""
Mangal Dosha computation.

Dosha is present when Mars occupies houses 1, 2, 4, 7, 8, or 12 from the Lagna.

Severity:
  high   — house 7 or 8
  medium — house 1, 2, or 4
  mild   — house 12

Cancellations (hard rules only):
  mars_own_sign  — Mars in Aries or Scorpio
  mars_exalted   — Mars in Capricorn
  jupiter_aspect — Jupiter conjoins (house 1) or aspects (houses 5, 7, 9) Mars
"""

from app.models import KundaliChart, MangalDoshaCompatibility, MangalDoshaResult

_DOSHA_HOUSES = {1, 2, 4, 7, 8, 12}
_HIGH_HOUSES = {7, 8}
_MEDIUM_HOUSES = {1, 2, 4}
_MILD_HOUSES = {12}

_MARS_OWN_SIGNS = {"Aries", "Scorpio"}
_MARS_EXALTED_SIGN = "Capricorn"
_JUPITER_ASPECT_HOUSES = {1, 5, 7, 9}


def _severity(house: int) -> str | None:
    if house in _HIGH_HOUSES:
        return "high"
    if house in _MEDIUM_HOUSES:
        return "medium"
    if house in _MILD_HOUSES:
        return "mild"
    return None


def compute_mangal_dosha(chart: KundaliChart) -> MangalDoshaResult:
    mars = chart.planets["mars"]
    mars_house = mars.house  # already computed from Lagna in planets_calculation

    has_dosha = mars_house in _DOSHA_HOUSES
    severity = _severity(mars_house) if has_dosha else None

    cancellation_reasons: list[str] = []

    if mars.zodiac in _MARS_OWN_SIGNS:
        cancellation_reasons.append("mars_own_sign")
    elif mars.zodiac == _MARS_EXALTED_SIGN:
        cancellation_reasons.append("mars_exalted")

    jupiter = chart.planets["jupiter"]
    mars_house_from_jupiter = (mars.house - jupiter.house) % 12 + 1
    if mars_house_from_jupiter in _JUPITER_ASPECT_HOUSES:
        cancellation_reasons.append("jupiter_aspect")

    cancelled = has_dosha and len(cancellation_reasons) > 0

    return MangalDoshaResult(
        has_dosha=has_dosha,
        mars_house=mars_house,
        severity=severity,
        cancelled=cancelled,
        cancellation_reasons=cancellation_reasons,
        mars_sign=mars.zodiac,
    )


def _determine_pairing(user: MangalDoshaResult, partner: MangalDoshaResult) -> str:
    user_active = user.has_dosha and not user.cancelled
    partner_active = partner.has_dosha and not partner.cancelled
    if not user_active and not partner_active:
        return "none"
    if user_active and partner_active:
        return "balanced"
    return "asymmetric"


def compute_mangal_dosha_compatibility(
    user_chart: KundaliChart,
    partner_chart: KundaliChart,
) -> MangalDoshaCompatibility:
    user_result = compute_mangal_dosha(user_chart)
    partner_result = compute_mangal_dosha(partner_chart)
    return MangalDoshaCompatibility(
        user=user_result,
        partner=partner_result,
        pairing=_determine_pairing(user_result, partner_result),
    )
