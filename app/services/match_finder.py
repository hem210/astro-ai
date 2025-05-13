from app.models import AshtakootaProfile
from app.services.ashtakoota_services.generate_profile import generate_ashtakoota_profile
from app.services.ashtakoota_services.calculate_score import calculate_ashtakoota

rashi_nakshatra_combinations = [
    ("Aries", "Ashwini", ["Chu", "Che", "Cho", "La"]),
    ("Aries", "Bharani", ["Lee", "Lu", "Le", "Lo"]),
    ("Aries", "Krittika", ["A", "E", "U", "Ea"]),
    ("Taurus", "Krittika", ["A", "E", "U", "Ea"]),
    ("Taurus", "Rohini", ["O", "Va", "Vi", "Vu"]),
    ("Taurus", "Mrigashira", ["Ve", "Vo", "Ka", "Ki"]),
    ("Gemini", "Mrigashira", ["Ve", "Vo", "Ka", "Ki"]),
    ("Gemini", "Ardra", ["Ku", "Gha", "Na", "Cha"]),
    ("Gemini", "Punarvasu", ["Ke", "Ko", "Ha", "Hi"]),
    ("Cancer", "Punarvasu", ["Ke", "Ko", "Ha", "Hi"]),
    ("Cancer", "Pushya", ["Hu", "He", "Ho", "Da"]),
    ("Cancer", "Ashlesha", ["De", "Du", "Dee", "Do"]),
    ("Leo", "Magha", ["Ma", "Mi", "Mu", "Me"]),
    ("Leo", "Purva Phalguni", ["Mo", "Ta", "Ti", "Tu"]),
    ("Leo", "Uttara Phalguni", ["Te", "To", "Pa", "Pi"]),
    ("Virgo", "Uttara Phalguni", ["Te", "To", "Pa", "Pi"]),
    ("Virgo", "Hasta", ["Pu", "Sha", "Na", "Tha"]),
    ("Virgo", "Chitra", ["Pe", "Po", "Ra", "Re"]),
    ("Libra", "Chitra", ["Pe", "Po", "Ra", "Re"]),
    ("Libra", "Swati", ["Ru", "Re", "Ro", "Ta"]),
    ("Libra", "Visakha", ["Ti", "Tu", "Te", "To"]),
    ("Scorpio", "Visakha", ["Ti", "Tu", "Te", "To"]),
    ("Scorpio", "Anuradha", ["Na", "Ni", "Nu", "Ne"]),
    ("Scorpio", "Jyeshtha", ["No", "Ya", "Yi", "Yu"]),
    ("Sagittarius", "Mula", ["Ye", "Yo", "Ba", "Be"]),
    ("Sagittarius", "Purva Ashadha", ["Bhu", "Dha", "Pha", "Dha"]),
    ("Sagittarius", "Uttara Ashadha", ["Bhe", "Bo", "Ja", "Ji"]),
    ("Capricorn", "Uttara Ashadha", ["Bhe", "Bo", "Ja", "Ji"]),
    ("Capricorn", "Shravana", ["Ju", "Je", "Jo", "Gha"]),
    ("Capricorn", "Dhanishta", ["Ga", "Gi", "Gu", "Ge"]),
    ("Aquarius", "Dhanishta", ["Ga", "Gi", "Gu", "Ge"]),
    ("Aquarius", "Shatabhisha", ["Go", "Sa", "Si", "Su"]),
    ("Aquarius", "Purva Bhadrapada", ["Se", "So", "Da", "Di"]),
    ("Pisces", "Purva Bhadrapada", ["Se", "So", "Da", "Di"]),
    ("Pisces", "Uttara Bhadrapada", ["Du", "Tha", "Jha", "Da"]),
    ("Pisces", "Revati", ["De", "Do", "Cha", "Chi"])
]

def find_perfect_match(ashtakoota_profile: AshtakootaProfile, type: str):
    
    matches = []

    for rashi, nakshatra, letters in rashi_nakshatra_combinations:
        score = 0
        spouse_ashtakoota_profile = generate_ashtakoota_profile(rashi, 15, nakshatra)   # deviation is taken as 15
        if(type=="groom"):
            score = calculate_ashtakoota(groom_profile=ashtakoota_profile,
                                bride_profile=spouse_ashtakoota_profile).total
        else:
            score = calculate_ashtakoota(groom_profile=spouse_ashtakoota_profile,
                                bride_profile=ashtakoota_profile).total
        
        if score > 22:
            matches.append({
                "rashi": rashi,
                "nakshatra": nakshatra,
                "letters": letters,
                "score": score
            })

    return sorted(matches, key=lambda x: x['score'], reverse=True)
