from app.models import AshtakootaMatchScore, AshtakootaProfile

def calculate_varna_koota(groom_varna, bride_varna):
    varna_map = {
        "Brahmin": 1, "Kshatriya": 2, "Vaishya": 3, "Shudra": 4
    }
    if varna_map[groom_varna] >= varna_map[bride_varna]:
        return 1
    else:
        return 0

def calculate_vashya_koota(groom_vashya, bride_vashya):
    table = [
        [2, 0, 0, 0.5, 0],
        [1, 2, 1, 0.5, 1],
        [0.5, 1, 2, 1, 1],
        [0, 0, 0, 2, 0],
        [1, 1, 1, 0, 2]
    ]

    vashya_map = {
        "Dwipada": 1, "Chatushpada": 2, "Jalachara": 3, "Vanachara": 4, "Keeta": 5
    }

    return table[vashya_map[groom_vashya] - 1][vashya_map[bride_vashya] - 1]

def calculate_tara_koota(groom_tara, bride_tara):

    if bride_tara in [3, 5, 7]:
        if groom_tara in [3, 5, 7]:
            return 0
        else:
            return 1.5
    else:
        if groom_tara in [3, 5, 7]:
            return 1.5
        else:
            return 3

def calculate_yoni_koota(groom_yoni, bride_yoni):
    table = [
        [4, 2, 2, 3, 2, 2, 2, 1, 0, 1, 1, 3, 2, 1],
        [2, 4, 3, 3, 2, 2, 2, 2, 3, 1, 2, 3, 2, 0],
        [2, 3, 4, 2, 1, 2, 1, 3, 3, 1, 2, 0, 3, 1],
        [3, 3, 2, 4, 2, 1, 1, 1, 1, 2, 2, 2, 0, 2],
        [2, 2, 1, 2, 4, 2, 1, 2, 2, 1, 0, 2, 1, 1],
        [2, 2, 2, 1, 2, 4, 0, 2, 2, 1, 3, 3, 2, 1],
        [2, 2, 1, 1, 1, 0, 4, 2, 2, 2, 2, 2, 1, 2],
        [1, 2, 3, 1, 2, 2, 2, 4, 3, 0, 3, 2, 2, 1],
        [0, 3, 3, 1, 2, 2, 2, 3, 4, 1, 2, 2, 2, 2],
        [1, 1, 1, 2, 1, 1, 2, 0, 1, 4, 1, 1, 2, 1],
        [1, 2, 2, 2, 0, 3, 2, 3, 2, 1, 4, 2, 2, 1],
        [3, 3, 0, 2, 2, 3, 2, 2, 2, 1, 2, 4, 3, 2],
        [2, 2, 3, 0, 1, 2, 1, 2, 2, 2, 2, 3, 4, 2],
        [1, 0, 1, 2, 1, 1, 2, 1, 2, 1, 1, 2, 2, 4]
    ]

    yoni_map = {
        "Ashwa": 1, "Gaja": 2, "Mesha": 3, "Sarpa": 4, "Shwana": 5, "Marjar": 6, "Mushaka": 7,
        "Gau": 8, "Mahisha": 9, "Vyaghra": 10, "Mriga": 11, "Vanara": 12, "Nakula": 13, "Simha": 14
    }

    return table[yoni_map[groom_yoni] - 1][yoni_map[bride_yoni] - 1]

def calculate_graha_maitri_koota(groom_graha_maitri, bride_graha_maitri):
    friendship_chart = {
        "Sun":{
            "Friend": ["Sun", "Moon", "Mars", "Jupiter"],
            "Neutral": ["Mercury"],
            "Enemy": ["Venus", "Saturn"]
        },
        "Moon":{
            "Friend": ["Moon", "Sun", "Mercury"],
            "Neutral": ["Jupiter", "Venus", "Saturn", "Mars"],
            "Enemy": []
        },
        "Mars":{
            "Friend": ["Mars", "Sun", "Moon", "Jupiter"],
            "Neutral": ["Saturn", "Venus"],
            "Enemy": ["Mercury"]
        },
        "Mercury":{
            "Friend": ["Mercury", "Sun", "Venus"],
            "Neutral": ["Mars", "Jupiter", "Saturn"],
            "Enemy": ["Moon"]
        },
        "Jupiter":{
            "Friend": ["Jupiter", "Sun", "Moon", "Mars"],
            "Neutral": ["Saturn"],
            "Enemy": ["Mercury", "Venus"]
        },
        "Venus":{
            "Friend": ["Venus", "Mercury", "Saturn"],
            "Neutral": ["Mars", "Jupiter"],
            "Enemy": ["Sun", "Moon"]
        },
        "Saturn":{
            "Friend": ["Saturn", "Mercury", "Venus"],
            "Neutral": ["Jupiter"],
            "Enemy": ["Sun", "Moon", "Mars"]
        }
    }

    relation_1 = ""
    relation_2 = ""
    if bride_graha_maitri in friendship_chart[groom_graha_maitri]["Friend"]:
        relation_1 = "Friend"
    elif bride_graha_maitri in friendship_chart[groom_graha_maitri]["Neutral"]:
        relation_1 = "Neutral"
    else:
        relation_1 = "Enemy"
    
    if groom_graha_maitri in friendship_chart[bride_graha_maitri]["Friend"]:
        relation_2 = "Friend"
    elif groom_graha_maitri in friendship_chart[bride_graha_maitri]["Neutral"]:
        relation_2 = "Neutral"
    else:
        relation_2 = "Enemy"
    
    if {relation_1, relation_2} == {"Friend", "Friend"}:
        return 5
    elif {relation_1, relation_2} == {"Friend", "Neutral"}:
        return 4
    elif {relation_1, relation_2} == {"Neutral", "Neutral"}:
        return 3
    elif {relation_1, relation_2} == {"Friend", "Enemy"}:
        return 1
    elif {relation_1, relation_2} == {"Neutral", "Enemy"}:
        return 0.5
    else:
        return 0


def calculate_gana_koota(groom_gana, bride_gana):
    if (groom_gana == bride_gana) or (groom_gana == "Deva" and bride_gana == "Manushya"):
        return 6
    elif (groom_gana == "Manushya" and bride_gana == "Deva"):
        return 5
    elif (groom_gana == "Rakshasa" and bride_gana == "Deva"):
        return 1
    else:
        return 0

def calculate_bhakoota_koota(groom_bhakoota, bride_bhakoota):
    zodiac_map = {
        'Aries': 1, 'Taurus': 2, 'Gemini': 3, 'Cancer': 4, 'Leo': 5, 'Virgo': 6, 
        'Libra': 7, 'Scorpio': 8, 'Sagittarius': 9, 'Capricorn': 10, 'Aquarius': 11, 'Pisces': 12
    }
    diff = abs(zodiac_map[groom_bhakoota] - zodiac_map[bride_bhakoota]) + 1
    if diff in [1, 3, 4, 7, 10, 11]:
        return 7
    else:
        return 0


def calculate_nadi_koota(groom_nadi, bride_nadi):
    if groom_nadi == bride_nadi:
        return 0
    else:
        return 8
        

def calculate_ashtakoota(groom_profile: AshtakootaProfile, bride_profile: AshtakootaProfile) -> AshtakootaMatchScore:
    match_score = AshtakootaMatchScore()
    match_score.varna = calculate_varna_koota(groom_profile.varna, bride_profile.varna)
    match_score.vashya = calculate_vashya_koota(groom_profile.vashya, bride_profile.vashya)
    match_score.tara = calculate_tara_koota(groom_profile.tara, bride_profile.tara)
    match_score.yoni = calculate_yoni_koota(groom_profile.yoni, bride_profile.yoni)
    match_score.graha_maitri = calculate_graha_maitri_koota(groom_profile.graha_maitri, bride_profile.graha_maitri)
    match_score.gana = calculate_gana_koota(groom_profile.gana, bride_profile.gana)
    match_score.bhakoota = calculate_bhakoota_koota(groom_profile.bhakoota, bride_profile.bhakoota)
    match_score.nadi = calculate_nadi_koota(groom_profile.nadi, bride_profile.nadi)

    match_score.total = sum([
        match_score.varna, match_score.vashya, match_score.tara, match_score.yoni,
        match_score.graha_maitri, match_score.gana, match_score.bhakoota, match_score.nadi
    ])
    return match_score
