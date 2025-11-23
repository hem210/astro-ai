#!/usr/bin/env python3
"""
Vedic Astrology Knowledge Base Generator

This script generates a comprehensive JSON knowledge base containing interpretations
for all planet-house and planet-sign combinations in Vedic astrology using Claude 4.5 Sonnet.
"""

import argparse
import json
import logging
import os
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from litellm import completion

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_FILE = PROJECT_ROOT / "app" / "data" / "vedic_knowledge_base.json"
LOG_FILE = SCRIPT_DIR / "knowledge_base_generation.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Vedic Astrology Constants
PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "rahu", "ketu"]
SIGNS = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", 
         "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
HOUSES = list(range(1, 13))

# Exaltation and Debilitation mappings
EXALTATION_DEBILITATION = {
    "sun": {"exalted": "aries", "debilitated": "libra"},
    "moon": {"exalted": "taurus", "debilitated": "scorpio"},
    "mercury": {"exalted": "virgo", "debilitated": "pisces"},
    "venus": {"exalted": "pisces", "debilitated": "virgo"},
    "mars": {"exalted": "capricorn", "debilitated": "cancer"},
    "jupiter": {"exalted": "cancer", "debilitated": "capricorn"},
    "saturn": {"exalted": "libra", "debilitated": "aries"},
    "rahu": {},  # Shadow planet, no exaltation/debilitation
    "ketu": {}   # Shadow planet, no exaltation/debilitation
}

# House Significations
HOUSE_SIGNIFICATIONS = {
    1: "Self, personality, physical appearance, head, overall health and vitality",
    2: "Wealth, family, speech, food, face, eyes, education, accumulated resources",
    3: "Siblings, courage, communication, short journeys, hands, writing, skills",
    4: "Home, mother, property, vehicles, education, comfort, inner peace",
    5: "Children, creativity, education, intelligence, speculation, romance",
    6: "Enemies, diseases, debts, service, competition, obstacles, health issues",
    7: "Marriage, spouse, partnerships, business, public relations, genitals",
    8: "Longevity, transformation, occult, inheritance, sudden events, mysteries",
    9: "Father, dharma, higher learning, philosophy, fortune, long journeys, guru",
    10: "Career, profession, reputation, status, authority, knees, public image",
    11: "Gains, income, friends, elder siblings, aspirations, fulfillment of desires",
    12: "Expenses, losses, foreign lands, spirituality, isolation, bed pleasures, moksha"
}

# Planetary Nature
PLANETARY_NATURE = {
    "sun": "Malefic",
    "moon": "Benefic",
    "mercury": "Mixed",
    "venus": "Benefic",
    "mars": "Malefic",
    "jupiter": "Benefic",
    "saturn": "Malefic",
    "rahu": "Malefic",
    "ketu": "Malefic"
}

# Planetary Aspects (houses from planet's position)
PLANETARY_ASPECTS = {
    "sun": [7],  # 7th house aspect
    "moon": [7],  # 7th house aspect
    "mercury": [7],  # 7th house aspect
    "venus": [7],  # 7th house aspect
    "mars": [4, 7, 8],  # 4th, 7th, 8th house aspects
    "jupiter": [5, 7, 9],  # 5th, 7th, 9th house aspects
    "saturn": [3, 7, 10],  # 3rd, 7th, 10th house aspects
    "rahu": [5, 7, 9],  # Similar to Jupiter
    "ketu": [5, 7, 9]  # Similar to Jupiter
}

# System Prompt
SYSTEM_PROMPT = """You are an expert Scholar of Vedic Astrology (Jyotish Shastra).

Your task is to generate interpretation data for a database.

RULES:

1. IGNORE Western Tropical attributes. Use strictly Sidereal/Vedic definitions.
   - Example: Sun in Libra is Debilitated (Weak), not just "Charming."
   - Example: Saturn in Aries is Debilitated (Frustrated), not "Bold."

2. TONE: Modern, psychological, empathetic, but truthful.
   - Avoid fatalistic language like "You will die" or "You will be poor."
   - Instead, use growth-oriented language: "You grow through challenges" or "You learn to manage resources."
   - Be actionable and empowering while remaining authentic to Vedic principles.

3. FORMAT: Return ONLY valid JSON. No markdown, no explanations, just the JSON object.

4. STRUCTURE: The JSON must have these exact keys:
   - archetype: A short, memorable title (e.g., "The Protective Commander")
   - strengths: An array of exactly 3 strings, each describing a strength
   - challenges: An array of exactly 3 strings, each describing a challenge
   - behavioral_advice: A single sentence providing actionable advice
   - vedic_concepts: An object with:
     - exaltation_status: "exalted", "debilitated", or "neutral"
     - house_signification: Brief description of what the house represents
     - planetary_nature: "Benefic", "Malefic", or "Mixed"
"""


class RateLimiter:
    """Rate limiter for API calls: 50 requests per minute"""
    
    def __init__(self, max_requests: int = 50, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times = deque()
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove requests older than the time window
        while self.request_times and self.request_times[0] < now - self.time_window:
            self.request_times.popleft()
        
        # If we're at the limit, wait until the oldest request expires
        if len(self.request_times) >= self.max_requests:
            sleep_time = self.time_window - (now - self.request_times[0]) + 0.1
            logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
            # Clean up again after waiting
            now = time.time()
            while self.request_times and self.request_times[0] < now - self.time_window:
                self.request_times.popleft()
        
        # Record this request
        self.request_times.append(time.time())


def get_exaltation_status(planet: str, sign: Optional[str] = None) -> str:
    """Determine exaltation status for a planet in a sign"""
    if planet not in EXALTATION_DEBILITATION:
        return "neutral"
    
    exalt_info = EXALTATION_DEBILITATION[planet]
    if not exalt_info:  # Rahu/Ketu
        return "neutral"
    
    if sign:
        sign_lower = sign.lower()
        if exalt_info.get("exalted") == sign_lower:
            return "exalted"
        elif exalt_info.get("debilitated") == sign_lower:
            return "debilitated"
    
    return "neutral"


def generate_user_prompt(planet: str, combination_type: str, value: str) -> str:
    """Generate user prompt for LLM based on combination type"""
    planet_capitalized = planet.capitalize()
    
    if combination_type == "house":
        house_num = int(value)
        house_sig = HOUSE_SIGNIFICATIONS[house_num]
        exalt_status = "neutral"  # Houses don't have exaltation status
        
        prompt = f"""Generate the JSON entry for **{planet_capitalized} in the {house_num}{get_ordinal_suffix(house_num)} House**.

Context:
- House Signification: {house_sig}
- Planetary Nature: {PLANETARY_NATURE[planet]}
- Exaltation Status: {exalt_status} (houses don't have exaltation, only signs do)

Schema:
{{
  "archetype": "Short title (e.g., The Protective Commander)",
  "strengths": ["list", "of", "3", "points"],
  "challenges": ["list", "of", "3", "points"],
  "behavioral_advice": "One sentence actionable advice.",
  "vedic_concepts": {{
    "exaltation_status": "neutral",
    "house_signification": "{house_sig}",
    "planetary_nature": "{PLANETARY_NATURE[planet]}"
  }}
}}"""
    
    else:  # sign
        sign_capitalized = value.capitalize()
        exalt_status = get_exaltation_status(planet, value)
        
        prompt = f"""Generate the JSON entry for **{planet_capitalized} in {sign_capitalized}**.

Context:
- Exaltation Status: {exalt_status}
- Planetary Nature: {PLANETARY_NATURE[planet]}
- Sign: {sign_capitalized} (Vedic/Sidereal definition)

Schema:
{{
  "archetype": "Short title (e.g., The Protective Commander)",
  "strengths": ["list", "of", "3", "points"],
  "challenges": ["list", "of", "3", "points"],
  "behavioral_advice": "One sentence actionable advice.",
  "vedic_concepts": {{
    "exaltation_status": "{exalt_status}",
    "house_signification": "N/A (sign combination)",
    "planetary_nature": "{PLANETARY_NATURE[planet]}"
  }}
}}"""
    
    return prompt


def get_ordinal_suffix(n: int) -> str:
    """Get ordinal suffix (st, nd, rd, th)"""
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def generate_key(planet: str, combination_type: str, value: str) -> str:
    """Generate JSON key for the combination"""
    if combination_type == "house":
        return f"{planet}_{value}_house"
    else:  # sign
        return f"{planet}_{value.lower()}"


def call_llm(planet: str, combination_type: str, value: str, rate_limiter: RateLimiter) -> Optional[Dict]:
    """Call LLM to generate interpretation for a combination"""
    rate_limiter.wait_if_needed()
    
    user_prompt = generate_user_prompt(planet, combination_type, value)
    
    try:
        response = completion(
            model="claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON if wrapped in markdown code blocks
        if content.startswith("```"):
            # Remove markdown code block markers
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else content
        
        # Parse JSON
        result = json.loads(content)
        
        # Validate structure
        required_keys = ["archetype", "strengths", "challenges", "behavioral_advice", "vedic_concepts"]
        for key in required_keys:
            if key not in result:
                raise ValueError(f"Missing required key: {key}")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for {planet} {combination_type} {value}: {e}")
        logger.error(f"Response content: {content[:500]}")
        return None
    except Exception as e:
        logger.error(f"Error generating interpretation for {planet} {combination_type} {value}: {e}")
        return None


def generate_single_combination(planet: str, combination_type: str, value: str) -> Dict:
    """Generate interpretation for a single combination (test mode)"""
    rate_limiter = RateLimiter()
    
    logger.info(f"Generating interpretation for {planet} {combination_type} {value}...")
    result = call_llm(planet, combination_type, value, rate_limiter)
    
    if result:
        key = generate_key(planet, combination_type, value)
        return {key: result}
    else:
        logger.error(f"Failed to generate interpretation for {planet} {combination_type} {value}")
        return {}


def generate_all_combinations(output_file: Path, existing: Optional[Dict] = None) -> Dict:
    """Generate all planet-house and planet-sign combinations"""
    knowledge_base = existing.copy() if existing else {}
    rate_limiter = RateLimiter()
    total_combinations = len(PLANETS) * len(HOUSES) + len(PLANETS) * len(SIGNS)
    current = 0
    
    logger.info(f"Starting generation of {total_combinations} combinations...")
    if existing:
        logger.info(f"Resuming with {len(existing)} existing entries")
    
    # Generate planet-house combinations
    logger.info("Generating planet-house combinations...")
    for planet in PLANETS:
        for house in HOUSES:
            current += 1
            key = generate_key(planet, "house", str(house))
            
            if key in knowledge_base:
                logger.info(f"[{current}/{total_combinations}] Skipping {key} (already exists)")
                continue
            
            logger.info(f"[{current}/{total_combinations}] Generating {key}...")
            result = call_llm(planet, "house", str(house), rate_limiter)
            
            if result:
                knowledge_base[key] = result
                # Save incrementally
                save_knowledge_base(knowledge_base, output_file)
            else:
                logger.warning(f"Failed to generate {key}, continuing...")
    
    # Generate planet-sign combinations
    logger.info("Generating planet-sign combinations...")
    for planet in PLANETS:
        for sign in SIGNS:
            current += 1
            key = generate_key(planet, "sign", sign)
            
            if key in knowledge_base:
                logger.info(f"[{current}/{total_combinations}] Skipping {key} (already exists)")
                continue
            
            logger.info(f"[{current}/{total_combinations}] Generating {key}...")
            result = call_llm(planet, "sign", sign, rate_limiter)
            
            if result:
                knowledge_base[key] = result
                # Save incrementally
                save_knowledge_base(knowledge_base, output_file)
            else:
                logger.warning(f"Failed to generate {key}, continuing...")
    
    logger.info(f"Generation complete! Generated {len(knowledge_base)} combinations.")
    return knowledge_base


def save_knowledge_base(knowledge_base: Dict, output_file: Path):
    """Save knowledge base to JSON file"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
    logger.debug(f"Saved {len(knowledge_base)} entries to {output_file}")


def load_existing_knowledge_base(output_file: Path) -> Dict:
    """Load existing knowledge base if it exists"""
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing knowledge base: {e}")
    return {}


def parse_test_args(args: List[str]) -> Tuple[str, str, str]:
    """Parse test mode arguments"""
    if len(args) < 2:
        raise ValueError("Test mode requires: planet and house/sign")
    
    planet = args[0].lower()
    if planet not in PLANETS:
        raise ValueError(f"Invalid planet: {planet}. Must be one of {PLANETS}")
    
    value = args[1].lower()
    
    # Check if it's a house (numeric or with "house" suffix)
    if value.isdigit() or value.replace("th", "").replace("st", "").replace("nd", "").replace("rd", "").isdigit():
        house_num = int(value.replace("th", "").replace("st", "").replace("nd", "").replace("rd", ""))
        if house_num not in HOUSES:
            raise ValueError(f"Invalid house: {house_num}. Must be 1-12")
        return planet, "house", str(house_num)
    
    # Check if it's a sign
    if value in SIGNS:
        return planet, "sign", value
    
    # Check if it ends with "_house"
    if value.endswith("_house"):
        house_str = value.replace("_house", "")
        if house_str.isdigit():
            house_num = int(house_str)
            if house_num in HOUSES:
                return planet, "house", str(house_num)
    
    raise ValueError(f"Invalid value: {value}. Must be a house number (1-12) or sign name ({SIGNS})")


def main():
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable is not set.")
        logger.error("Please set it in your .env file or environment before running this script.")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="Generate Vedic Astrology Knowledge Base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode - single combination
  python scripts/generate_knowledge_base.py --test mars 4
  python scripts/generate_knowledge_base.py --test sun aries
  
  # Full generation
  python scripts/generate_knowledge_base.py
  
Note: Requires ANTHROPIC_API_KEY environment variable to be set.
        """
    )
    
    parser.add_argument(
        '--test',
        nargs='+',
        metavar=('PLANET', 'HOUSE_OR_SIGN'),
        help='Test mode: generate a single combination (e.g., --test mars 4 or --test sun aries)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=str(OUTPUT_FILE),
        help=f'Output file path (default: {OUTPUT_FILE})'
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    
    if args.test:
        # Test mode
        try:
            planet, combo_type, value = parse_test_args(args.test)
            result = generate_single_combination(planet, combo_type, value)
            
            if result:
                print("\n" + "="*80)
                print("Generated Interpretation:")
                print("="*80)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("="*80)
            else:
                logger.error("Failed to generate interpretation")
                sys.exit(1)
        except ValueError as e:
            logger.error(f"Invalid arguments: {e}")
            sys.exit(1)
    else:
        # Full generation mode
        logger.info("Starting full knowledge base generation...")
        logger.info(f"Output file: {output_path}")
        
        # Load existing knowledge base to resume
        existing = load_existing_knowledge_base(output_path)
        if existing:
            logger.info(f"Found existing knowledge base with {len(existing)} entries. Will skip existing entries.")
        
        # Generate all combinations
        knowledge_base = generate_all_combinations(output_path, existing)
        
        # Final save
        save_knowledge_base(knowledge_base, output_path)
        logger.info(f"Knowledge base saved to {output_path}")
        logger.info(f"Total entries: {len(knowledge_base)}")


if __name__ == "__main__":
    main()

