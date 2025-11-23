#!/usr/bin/env python3
"""
Additional Vedic Astrology Knowledge Base Generator

This script generates:
1. Ascendant profiles for 12 signs
2. Moon nakshatra interpretations (27 nakshatras)
3. Planetary conjunctions (all 2-planet combinations)

Uses Claude 4.5 Sonnet via litellm with rate limiting.
"""

import json
import logging
import os
import re
import sys
import time
from collections import deque
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional

from litellm import completion

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
OUTPUT_FILE = PROJECT_ROOT / "app" / "data" / "vedic_knowledge_base.json"
LOG_FILE = SCRIPT_DIR / "additional_knowledge_base_generation.log"

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
SIGNS = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", 
         "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Visakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "rahu", "ketu"]

# System Prompt
SYSTEM_PROMPT = """You are an expert Scholar of Vedic Astrology (Jyotish Shastra).

Your task is to generate interpretation data for a database.

RULES:

1. IGNORE Western Tropical attributes. Use strictly Sidereal/Vedic definitions.

2. TONE: Modern, psychological, empathetic, but truthful.
   - Avoid fatalistic language like "You will die" or "You will be poor."
   - Instead, use growth-oriented language: "You grow through challenges" or "You learn to manage resources."
   - Be actionable and empowering while remaining authentic to Vedic principles.

3. FORMAT: Return ONLY valid JSON. Do NOT wrap it in markdown code blocks (no ```json or ```). 
   Return the raw JSON object directly, starting with { and ending with }.
   No markdown, no explanations, no code block markers - just the pure JSON object.

4. Be specific and detailed in your interpretations, drawing from traditional Vedic texts while making them accessible and relevant to modern life.
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


def generate_ascendant_prompt(sign: str) -> str:
    """Generate prompt for ascendant profile"""
    sign_capitalized = sign.capitalize()
    
    prompt = f"""Generate the JSON entry for **Ascendant in {sign_capitalized}**.

In Vedic astrology, the Ascendant (Lagna) represents the self, physical appearance, personality, and how one presents to the world. Each sign as ascendant has functional benefics and malefics based on the sign's natural ruler.

Schema:
{{
  "key": "ascendant_{sign}",
  "physical_appearance": "Description of typical physical characteristics",
  "personality_traits": "Key personality traits and behavioral patterns",
  "functional_benefics": ["List", "of", "planets", "that", "act", "as", "benefics"],
  "functional_malefics": ["List", "of", "planets", "that", "act", "as", "malefics"],
  "key_life_lesson": "The main life lesson or karmic theme for this ascendant"
}}

Note: Functional benefics/malefics are determined by the sign's natural ruler and its relationships. Use traditional Vedic principles."""
    
    return prompt


def generate_nakshatra_prompt(nakshatra: str) -> str:
    """Generate prompt for nakshatra interpretation"""
    nakshatra_lower = nakshatra.lower().replace(" ", "_")
    
    prompt = f"""Generate the JSON entry for **Nakshatra: {nakshatra}**.

Nakshatras are the 27 lunar mansions in Vedic astrology. Each nakshatra has a symbol, deity, psychological nature, and specific characteristics.

Schema:
{{
  "key": "nakshatra_{nakshatra_lower}",
  "symbol": "The symbolic representation (e.g., The Coiled Serpent)",
  "deity": "The ruling deity",
  "psychological_nature": "Core psychological traits and tendencies",
  "strengths": ["List", "of", "key", "strengths"],
  "shadow_side": ["List", "of", "challenges", "or", "shadow", "aspects"],
  "activation_age": "Approximate age when this nakshatra's energy becomes prominent (e.g., Early 20s, Mid-30s, etc.)"
}}

Provide deep, insightful interpretations based on traditional Vedic texts."""
    
    return prompt


def generate_conjunction_prompt(planet1: str, planet2: str) -> str:
    """Generate prompt for planetary conjunction"""
    # Sort alphabetically to ensure consistent key generation
    planets_sorted = sorted([planet1, planet2])
    planet1_cap = planets_sorted[0].capitalize()
    planet2_cap = planets_sorted[1].capitalize()
    key = f"conjunction_{planets_sorted[0]}_{planets_sorted[1]}"
    
    prompt = f"""Generate the JSON entry for **Planetary Conjunction: {planet1_cap} and {planet2_cap}**.

In Vedic astrology, when two planets are in the same sign or very close (within a few degrees), they form a conjunction. This creates a blending of their energies, which can be harmonious or challenging depending on the planets involved.

Schema:
{{
  "key": "{key}",
  "theme": "The core theme or dynamic of this conjunction",
  "interpretation": "Detailed interpretation of how these planetary energies combine",
  "advice": "Practical, actionable advice for working with this conjunction"
}}

Consider:
- The natural relationship between these planets (friendship, enmity, neutral)
- How their energies blend or conflict
- The psychological and karmic implications
- Practical life manifestations"""
    
    return prompt


def extract_json_from_markdown(content: str) -> str:
    """Extract JSON from markdown code blocks if present"""
    content = content.strip()
    
    # Check if content starts with a code block marker
    if not content.startswith("```"):
        return content
    
    # Remove opening marker (```json or ```)
    if content.startswith("```json"):
        content = content[7:]  # Remove ```json
    elif content.startswith("```"):
        content = content[3:]  # Remove ```
    
    # Remove leading whitespace/newlines
    content = content.lstrip()
    
    # Remove closing marker if present (search from end)
    # Find the last occurrence of ``` that's not at the start
    last_backtick_idx = content.rfind("```")
    if last_backtick_idx > 0:  # Found closing marker and it's not at position 0
        content = content[:last_backtick_idx]
    
    # Remove trailing whitespace
    content = content.rstrip()
    
    return content


def call_llm(prompt: str, rate_limiter: RateLimiter) -> Optional[Dict]:
    """Call LLM to generate interpretation"""
    rate_limiter.wait_if_needed()
    
    raw_content = None
    content = None
    
    try:
        response = completion(
            model="claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        raw_content = response.choices[0].message.content.strip()
        
        # Extract JSON from markdown code blocks if present
        content = extract_json_from_markdown(raw_content)
        
        # Log if extraction happened (for debugging)
        if raw_content != content and raw_content.startswith("```"):
            logger.debug(f"Extracted JSON from markdown code block")
        
        # Parse JSON
        result = json.loads(content)
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        if raw_content:
            logger.error(f"Raw response (first 500 chars): {raw_content[:500]}")
        if content:
            logger.error(f"Extracted content (first 500 chars): {content[:500]}")
        else:
            logger.error(f"Content extraction failed or returned empty string")
        return None
    except Exception as e:
        logger.error(f"Error generating interpretation: {e}")
        return None


def generate_ascendant_profiles(rate_limiter: RateLimiter, existing: Dict) -> Dict:
    """Generate ascendant profiles for all 12 signs"""
    logger.info("Generating ascendant profiles...")
    knowledge_base = existing.copy()
    total = len(SIGNS)
    
    for idx, sign in enumerate(SIGNS, 1):
        key = f"ascendant_{sign}"
        
        if key in knowledge_base:
            logger.info(f"[{idx}/{total}] Skipping {key} (already exists)")
            continue
        
        logger.info(f"[{idx}/{total}] Generating {key}...")
        prompt = generate_ascendant_prompt(sign)
        result = call_llm(prompt, rate_limiter)
        
        if result:
            knowledge_base[key] = result
            save_knowledge_base(knowledge_base)
        else:
            logger.warning(f"Failed to generate {key}, continuing...")
    
    logger.info(f"Completed ascendant profiles. Total entries: {len([k for k in knowledge_base.keys() if k.startswith('ascendant_')])}")
    return knowledge_base


def generate_nakshatra_interpretations(rate_limiter: RateLimiter, existing: Dict) -> Dict:
    """Generate nakshatra interpretations for all 27 nakshatras"""
    logger.info("Generating nakshatra interpretations...")
    knowledge_base = existing.copy()
    total = len(NAKSHATRAS)
    
    for idx, nakshatra in enumerate(NAKSHATRAS, 1):
        key = f"nakshatra_{nakshatra.lower().replace(' ', '_')}"
        
        if key in knowledge_base:
            logger.info(f"[{idx}/{total}] Skipping {key} (already exists)")
            continue
        
        logger.info(f"[{idx}/{total}] Generating {key}...")
        prompt = generate_nakshatra_prompt(nakshatra)
        result = call_llm(prompt, rate_limiter)
        
        if result:
            knowledge_base[key] = result
            save_knowledge_base(knowledge_base)
        else:
            logger.warning(f"Failed to generate {key}, continuing...")
    
    logger.info(f"Completed nakshatra interpretations. Total entries: {len([k for k in knowledge_base.keys() if k.startswith('nakshatra_')])}")
    return knowledge_base


def generate_planetary_conjunctions(rate_limiter: RateLimiter, existing: Dict) -> Dict:
    """Generate planetary conjunction interpretations for all 2-planet combinations"""
    logger.info("Generating planetary conjunctions...")
    knowledge_base = existing.copy()
    
    # Generate all 2-planet combinations
    planet_combinations = list(combinations(PLANETS, 2))
    total = len(planet_combinations)
    
    for idx, (planet1, planet2) in enumerate(planet_combinations, 1):
        # Sort alphabetically for consistent key generation
        planets_sorted = sorted([planet1, planet2])
        key = f"conjunction_{planets_sorted[0]}_{planets_sorted[1]}"
        
        if key in knowledge_base:
            logger.info(f"[{idx}/{total}] Skipping {key} (already exists)")
            continue
        
        logger.info(f"[{idx}/{total}] Generating {key}...")
        prompt = generate_conjunction_prompt(planet1, planet2)
        result = call_llm(prompt, rate_limiter)
        
        if result:
            knowledge_base[key] = result
            save_knowledge_base(knowledge_base)
        else:
            logger.warning(f"Failed to generate {key}, continuing...")
    
    logger.info(f"Completed planetary conjunctions. Total entries: {len([k for k in knowledge_base.keys() if k.startswith('conjunction_')])}")
    return knowledge_base


def save_knowledge_base(knowledge_base: Dict):
    """Save knowledge base to JSON file"""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
    logger.debug(f"Saved {len(knowledge_base)} entries to {OUTPUT_FILE}")


def load_existing_knowledge_base() -> Dict:
    """Load existing knowledge base if it exists"""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load existing knowledge base: {e}")
    return {}


def main():
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable is not set.")
        logger.error("Please set it in your .env file or environment before running this script.")
        sys.exit(1)
    
    logger.info("Starting additional knowledge base generation...")
    logger.info(f"Output file: {OUTPUT_FILE}")
    
    # Load existing knowledge base
    existing = load_existing_knowledge_base()
    if existing:
        logger.info(f"Found existing knowledge base with {len(existing)} entries. Will append new entries.")
    
    rate_limiter = RateLimiter()
    knowledge_base = existing.copy()
    
    # Generate all three types
    logger.info("="*80)
    logger.info("1. GENERATING ASCENDANT PROFILES")
    logger.info("="*80)
    knowledge_base = generate_ascendant_profiles(rate_limiter, knowledge_base)
    
    logger.info("="*80)
    logger.info("2. GENERATING NAKSHATRA INTERPRETATIONS")
    logger.info("="*80)
    knowledge_base = generate_nakshatra_interpretations(rate_limiter, knowledge_base)
    
    logger.info("="*80)
    logger.info("3. GENERATING PLANETARY CONJUNCTIONS")
    logger.info("="*80)
    knowledge_base = generate_planetary_conjunctions(rate_limiter, knowledge_base)
    
    # Final save
    save_knowledge_base(knowledge_base)
    logger.info("="*80)
    logger.info(f"Generation complete! Knowledge base saved to {OUTPUT_FILE}")
    logger.info(f"Total entries: {len(knowledge_base)}")
    logger.info("="*80)
    
    # Summary
    ascendant_count = len([k for k in knowledge_base.keys() if k.startswith('ascendant_')])
    nakshatra_count = len([k for k in knowledge_base.keys() if k.startswith('nakshatra_')])
    conjunction_count = len([k for k in knowledge_base.keys() if k.startswith('conjunction_')])
    
    logger.info(f"Summary:")
    logger.info(f"  - Ascendant profiles: {ascendant_count}/12")
    logger.info(f"  - Nakshatra interpretations: {nakshatra_count}/27")
    logger.info(f"  - Planetary conjunctions: {conjunction_count}/36")


if __name__ == "__main__":
    main()

