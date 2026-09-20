from app.models import AshtakootaProfile, AshtakootaMatchScore
from app.services.ashtakoota_services.generate_profile import generate_ashtakoota_profile
from app.services.ashtakoota_services.calculate_score import calculate_ashtakoota

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

# All 36 rashi-nakshatra combinations (overlapping nakshatras appear twice)
RASHI_NAKSHATRA_COMBOS: list[tuple[str, str]] = [
    ("Aries",        "Ashwini"),
    ("Aries",        "Bharani"),
    ("Aries",        "Krittika"),
    ("Taurus",       "Krittika"),
    ("Taurus",       "Rohini"),
    ("Taurus",       "Mrigashira"),
    ("Gemini",       "Mrigashira"),
    ("Gemini",       "Ardra"),
    ("Gemini",       "Punarvasu"),
    ("Cancer",       "Punarvasu"),
    ("Cancer",       "Pushya"),
    ("Cancer",       "Ashlesha"),
    ("Leo",          "Magha"),
    ("Leo",          "Purva Phalguni"),
    ("Leo",          "Uttara Phalguni"),
    ("Virgo",        "Uttara Phalguni"),
    ("Virgo",        "Hasta"),
    ("Virgo",        "Chitra"),
    ("Libra",        "Chitra"),
    ("Libra",        "Swati"),
    ("Libra",        "Visakha"),
    ("Scorpio",      "Visakha"),
    ("Scorpio",      "Anuradha"),
    ("Scorpio",      "Jyeshtha"),
    ("Sagittarius",  "Mula"),
    ("Sagittarius",  "Purva Ashadha"),
    ("Sagittarius",  "Uttara Ashadha"),
    ("Capricorn",    "Uttara Ashadha"),
    ("Capricorn",    "Shravana"),
    ("Capricorn",    "Dhanishta"),
    ("Aquarius",     "Dhanishta"),
    ("Aquarius",     "Shatabhisha"),
    ("Aquarius",     "Purva Bhadrapada"),
    ("Pisces",       "Purva Bhadrapada"),
    ("Pisces",       "Uttara Bhadrapada"),
    ("Pisces",       "Revati"),
]

# Birth name syllables (namakarana aksharas) keyed by nakshatra
NAKSHATRA_SYLLABLES: dict[str, list[str]] = {
    "Ashwini":          ["Chu", "Che", "Cho", "La"],
    "Bharani":          ["Lee", "Lu", "Le", "Lo"],
    "Krittika":         ["A", "E", "U", "Ea"],
    "Rohini":           ["O", "Va", "Vi", "Vu"],
    "Mrigashira":       ["Ve", "Vo", "Ka", "Ki"],
    "Ardra":            ["Ku", "Gha", "Na", "Cha"],
    "Punarvasu":        ["Ke", "Ko", "Ha", "Hi"],
    "Pushya":           ["Hu", "He", "Ho", "Da"],
    "Ashlesha":         ["De", "Du", "Dee", "Do"],
    "Magha":            ["Ma", "Mi", "Mu", "Me"],
    "Purva Phalguni":   ["Mo", "Ta", "Ti", "Tu"],
    "Uttara Phalguni":  ["Te", "To", "Pa", "Pi"],
    "Hasta":            ["Pu", "Sha", "Na", "Tha"],
    "Chitra":           ["Pe", "Po", "Ra", "Re"],
    "Swati":            ["Ru", "Re", "Ro", "Ta"],
    "Visakha":          ["Ti", "Tu", "Te", "To"],
    "Anuradha":         ["Na", "Ni", "Nu", "Ne"],
    "Jyeshtha":         ["No", "Ya", "Yi", "Yu"],
    "Mula":             ["Ye", "Yo", "Ba", "Be"],
    "Purva Ashadha":    ["Bhu", "Dha", "Pha", "Dha"],
    "Uttara Ashadha":   ["Bhe", "Bo", "Ja", "Ji"],
    "Shravana":         ["Ju", "Je", "Jo", "Gha"],
    "Dhanishta":        ["Ga", "Gi", "Gu", "Ge"],
    "Shatabhisha":      ["Go", "Sa", "Si", "Su"],
    "Purva Bhadrapada": ["Se", "So", "Da", "Di"],
    "Uttara Bhadrapada":["Du", "Tha", "Jha", "Da"],
    "Revati":           ["De", "Do", "Cha", "Chi"],
}

# ---------------------------------------------------------------------------
# Match sweep
# ---------------------------------------------------------------------------

def nadi_dosha_info(
    person_rashi: str, person_nakshatra: str,
    candidate_rashi: str, candidate_nakshatra: str,
    nadi_score: float,
) -> dict | None:
    if nadi_score > 0:
        return None
    same_rashi = person_rashi == candidate_rashi
    same_nakshatra = person_nakshatra == candidate_nakshatra
    if same_rashi and not same_nakshatra:
        return {"cancelled": True, "cancellation_reason": "Same rashi, different nakshatra"}
    if same_nakshatra and not same_rashi:
        return {"cancelled": True, "cancellation_reason": "Same nakshatra, different rashi"}
    return {"cancelled": False, "cancellation_reason": None}


def bhakoota_dosha_info(bhakoota_score: float, graha_maitri_score: float) -> dict | None:
    if bhakoota_score > 0:
        return None
    if graha_maitri_score == 5:
        return {"cancelled": True, "cancellation_reason": "Graha Maitri is full (5/5)"}
    return {"cancelled": False, "cancellation_reason": None}


def find_best_matches(
    person_profile: AshtakootaProfile,
    gender: str,                          # "male" | "female"
) -> list[dict]:
    """
    Score all 36 rashi-nakshatra combinations against the person's profile.
    Returns all results sorted by score descending.
    Gender determines whether the person is treated as groom (male) or bride (female).
    """
    is_groom = gender.lower() == "male"
    results = []

    for rashi, nakshatra in RASHI_NAKSHATRA_COMBOS:
        candidate = generate_ashtakoota_profile(rashi, 15, nakshatra)

        if is_groom:
            score_obj: AshtakootaMatchScore = calculate_ashtakoota(
                groom_profile=person_profile,
                bride_profile=candidate,
            )
        else:
            score_obj: AshtakootaMatchScore = calculate_ashtakoota(
                groom_profile=candidate,
                bride_profile=person_profile,
            )

        results.append({
            "rashi":          rashi,
            "nakshatra":      nakshatra,
            "syllables":      NAKSHATRA_SYLLABLES[nakshatra],
            "score":          score_obj,
            "nadi_dosha":     nadi_dosha_info(
                                  person_profile.moon_zodiac, person_profile.nakshatra,
                                  rashi, nakshatra,
                                  score_obj.nadi,
                              ),
            "bhakoota_dosha": bhakoota_dosha_info(score_obj.bhakoota, score_obj.graha_maitri),
        })

    return sorted(results, key=lambda x: x["score"].total, reverse=True)
