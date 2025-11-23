"""
Knowledge Base Query Tool

This tool queries the Vedic astrology knowledge base for interpretations.
It supports queries for planets in houses, planets in signs, ascendant signs,
nakshatras, and planetary conjunctions.
"""

from langchain_core.tools import tool
from app.services.knowledge_base_service import get_knowledge_base_service
from typing import Dict, Any, Optional


@tool
def query_knowledge_base(
    query_type: str,
    planet: Optional[str] = None,
    sign: Optional[str] = None,
    house: Optional[int] = None,
    nakshatra: Optional[str] = None,
    planet1: Optional[str] = None,
    planet2: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Query the Vedic astrology knowledge base for interpretations.
    
    This tool retrieves astrological interpretations from the knowledge base.
    All inputs are automatically normalized to lowercase.
    
    Args:
        query_type: Type of query. Must be one of:
            - "planet_in_house": Get interpretation for a planet in a house
            - "planet_in_sign": Get interpretation for a planet in a sign
            - "ascendant_sign": Get interpretation for an ascendant sign
            - "nakshatra": Get interpretation for a nakshatra
            - "conjunction": Get interpretation for a planetary conjunction
        planet: Planet name (required for planet_in_house and planet_in_sign)
        sign: Zodiac sign (required for planet_in_sign and ascendant_sign)
        house: House number 1-12 (required for planet_in_house)
        nakshatra: Nakshatra name (required for nakshatra query)
        planet1: First planet name (required for conjunction)
        planet2: Second planet name (required for conjunction)
    
    Returns:
        Dictionary containing interpretation with keys:
        - archetype: Short title describing the combination
        - strengths: List of strengths
        - challenges: List of challenges
        - behavioral_advice: Actionable advice
        - vedic_concepts: Dictionary with exaltation_status, house_signification, planetary_nature
    
    Example:
        # Query planet in house
        query_knowledge_base(
            query_type="planet_in_house",
            planet="sun",
            house=1
        )
        
        # Query planet in sign
        query_knowledge_base(
            query_type="planet_in_sign",
            planet="moon",
            sign="cancer"
        )
        
        # Query ascendant sign
        query_knowledge_base(
            query_type="ascendant_sign",
            sign="aries"
        )
        
        # Query nakshatra
        query_knowledge_base(
            query_type="nakshatra",
            nakshatra="ashwini"
        )
        
        # Query conjunction
        query_knowledge_base(
            query_type="conjunction",
            planet1="sun",
            planet2="moon"
        )
    """
    kb_service = get_knowledge_base_service()
    query_type = query_type.lower().strip()
    
    if query_type == "planet_in_house":
        if not planet or house is None:
            return {"error": "planet and house are required for planet_in_house query"}
        result = kb_service.get_planet_in_house(planet, house)
    
    elif query_type == "planet_in_sign":
        if not planet or not sign:
            return {"error": "planet and sign are required for planet_in_sign query"}
        result = kb_service.get_planet_in_sign(planet, sign)
    
    elif query_type == "ascendant_sign":
        if not sign:
            return {"error": "sign is required for ascendant_sign query"}
        result = kb_service.get_ascendant_sign(sign)
    
    elif query_type == "nakshatra":
        if not nakshatra:
            return {"error": "nakshatra is required for nakshatra query"}
        result = kb_service.get_nakshatra(nakshatra)
    
    elif query_type == "conjunction":
        if not planet1 or not planet2:
            return {"error": "planet1 and planet2 are required for conjunction query"}
        result = kb_service.get_conjunction(planet1, planet2)
    
    else:
        return {
            "error": f"Invalid query_type: {query_type}. Must be one of: planet_in_house, planet_in_sign, ascendant_sign, nakshatra, conjunction"
        }
    
    if result is None:
        return {"error": "No interpretation found for the given parameters"}
    
    return result

