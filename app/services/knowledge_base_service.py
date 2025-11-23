"""
Knowledge Base Service for Vedic Astrology Interpretations

This service loads and queries the vedic_knowledge_base.json file,
providing normalized access to astrological interpretations.
All queries are normalized to lowercase for consistent access.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

# Path to knowledge base JSON file
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "data" / "vedic_knowledge_base.json"


class KnowledgeBaseService:
    """Service for querying the Vedic astrology knowledge base."""
    
    def __init__(self):
        """Initialize the service and load the knowledge base."""
        self._knowledge_base: Optional[Dict[str, Any]] = None
        self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> None:
        """Load the knowledge base JSON file."""
        try:
            with open(KNOWLEDGE_BASE_PATH, 'r', encoding='utf-8') as f:
                self._knowledge_base = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Knowledge base file not found at {KNOWLEDGE_BASE_PATH}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing knowledge base JSON: {e}")
    
    def get_planet_in_house(self, planet: str, house: int) -> Optional[Dict[str, Any]]:
        """
        Get interpretation for a planet in a specific house.
        
        Args:
            planet: Planet name (e.g., 'sun', 'moon', 'mars')
            house: House number (1-12)
        
        Returns:
            Interpretation dictionary or None if not found
        """
        planet = planet.lower().strip()
        key = f"{planet}_{house}_house"
        return self._knowledge_base.get(key)
    
    def get_planet_in_sign(self, planet: str, sign: str) -> Optional[Dict[str, Any]]:
        """
        Get interpretation for a planet in a specific sign.
        
        Args:
            planet: Planet name (e.g., 'sun', 'moon', 'mars')
            sign: Zodiac sign (e.g., 'aries', 'taurus', 'gemini')
        
        Returns:
            Interpretation dictionary or None if not found
        """
        planet = planet.lower().strip()
        sign = sign.lower().strip()
        key = f"{planet}_{sign}"
        return self._knowledge_base.get(key)
    
    def get_ascendant_sign(self, sign: str) -> Optional[Dict[str, Any]]:
        """
        Get interpretation for an ascendant sign.
        
        Args:
            sign: Zodiac sign (e.g., 'aries', 'taurus', 'gemini')
        
        Returns:
            Interpretation dictionary or None if not found
        """
        sign = sign.lower().strip()
        key = f"ascendant_{sign}"
        return self._knowledge_base.get(key)
    
    def get_nakshatra(self, nakshatra_name: str) -> Optional[Dict[str, Any]]:
        """
        Get interpretation for a nakshatra.
        
        Args:
            nakshatra_name: Nakshatra name (e.g., 'ashwini', 'bharani', 'rohini')
        
        Returns:
            Interpretation dictionary or None if not found
        """
        nakshatra_name = nakshatra_name.lower().strip()
        # Handle spaces in nakshatra names (e.g., "purva phalguni" -> "purva_phalguni")
        nakshatra_name = nakshatra_name.replace(" ", "_")
        key = f"nakshatra_{nakshatra_name}"
        return self._knowledge_base.get(key)
    
    def get_conjunction(self, planet1: str, planet2: str) -> Optional[Dict[str, Any]]:
        """
        Get interpretation for a conjunction of two planets.
        
        Args:
            planet1: First planet name (e.g., 'sun', 'moon')
            planet2: Second planet name (e.g., 'mars', 'jupiter')
        
        Returns:
            Interpretation dictionary or None if not found
        """
        planet1 = planet1.lower().strip()
        planet2 = planet2.lower().strip()
        # Try both orders since conjunction might be stored as planet1_planet2 or planet2_planet1
        key1 = f"conjunction_{planet1}_{planet2}"
        key2 = f"conjunction_{planet2}_{planet1}"
        
        result = self._knowledge_base.get(key1)
        if result is None:
            result = self._knowledge_base.get(key2)
        
        return result
    
    def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get interpretation by direct key lookup.
        
        Args:
            key: Knowledge base key (normalized to lowercase)
        
        Returns:
            Interpretation dictionary or None if not found
        """
        key = key.lower().strip()
        return self._knowledge_base.get(key)


# Global instance
_knowledge_base_service: Optional[KnowledgeBaseService] = None


def get_knowledge_base_service() -> KnowledgeBaseService:
    """Get or create the global knowledge base service instance."""
    global _knowledge_base_service
    if _knowledge_base_service is None:
        _knowledge_base_service = KnowledgeBaseService()
    return _knowledge_base_service

