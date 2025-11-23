from app.models import AshtakootaProfile

def calculate_varna(zodiac):
    if zodiac in ["Aries", "Leo", "Sagittarius"]:
        return "Kshatriya"
    elif zodiac in ["Taurus", "Virgo", "Capricorn"]:
        return "Vaishya"
    elif zodiac in ["Gemini", "Libra", "Aquarius"]:
        return "Shudra"
    elif zodiac in ["Cancer", "Scorpio", "Pisces"]:
        return "Brahmin"

def calculate_vashya(zodiac, deviate):
    if zodiac in ["Aries", "Taurus"]:
        return "Chatushpada"
    elif zodiac in ["Gemini", "Virgo", "Libra", "Aquarius"]:
        return "Dwipada"
    elif zodiac in ["Cancer", "Pisces"]:
        return "Jalachara"
    elif zodiac == "Leo":
        return "Vanachara"
    elif zodiac == "Scorpio":
        return "Keeta"
    elif zodiac == "Capricorn":
        if deviate <= 15:
            return "Chatushpada"
        else:
            return "Jalachara"
    elif zodiac == "Sagittarius":
        if deviate > 15:
            return "Chatushpada"
        else:
            return "Dwipada"

def calculate_tara(nakshatra):
    nakshatra_map = {
        'Ashwini': 1, 'Bharani':2, 'Krittika':3, 'Rohini':4, 'Mrigashira':5, 'Ardra':6, 
        'Punarvasu':7, 'Pushya':8, 'Ashlesha':9, 'Magha':10, 'Purva Phalguni':11, 'Uttara Phalguni':12,
        'Hasta':13, 'Chitra':14, 'Swati':15, 'Visakha':16, 'Anuradha':17, 'Jyeshtha':18, 
        'Mula':19, 'Purva Ashadha':20, 'Uttara Ashadha':21, 'Shravana':22, 'Dhanishta':23, 
        'Shatabhisha':24, 'Purva Bhadrapada':25, 'Uttara Bhadrapada':26, 'Revati':27
    }
    return (nakshatra_map[nakshatra] % 9) + 1

def calculate_yoni(nakshatra):
    if nakshatra in ["Ashwini", "Shatabhisha"]:
        return "Ashwa"
    elif nakshatra in ["Bharani", "Revati"]:
        return "Gaja"
    elif nakshatra in ["Krittika", "Pushya"]:
        return "Mesha"
    elif nakshatra in ["Rohini", "Mrigashira"]:
        return "Sarpa"
    elif nakshatra in ["Ardra", "Mula"]:
        return "Shwana"
    elif nakshatra in ["Punarvasu", "Ashlesha"]:
        return "Marjar"
    elif nakshatra in ["Magha", "Purva Phalguni"]:
        return "Mushaka"
    elif nakshatra in ["Uttara Phalguni", "Uttara Bhadrapada"]:
        return "Gau"
    elif nakshatra in ["Hasta", "Swati"]:
        return "Mahisha"
    elif nakshatra in ["Chitra", "Visakha"]:
        return "Vyaghra"
    elif nakshatra in ["Anuradha", "Jyeshtha"]:
        return "Mriga"
    elif nakshatra in ["Purva Ashadha", "Shravana"]:
        return "Vanara"
    elif nakshatra in ["Uttara Ashadha", "Abhijit"]:
        return "Nakula"
    elif nakshatra in ["Dhanishta", "Purva Bhadrapada"]:
        return "Simha"

def calculate_graha_maitri(zodiac):
    if zodiac in ["Aries", "Scorpio"]:
        return "Mars"
    elif zodiac in ["Taurus", "Libra"]:
        return "Venus"
    elif zodiac in ["Gemini", "Virgo"]:
        return "Mercury"
    elif zodiac in ["Cancer"]:
        return "Moon"
    elif zodiac in ["Leo"]:
        return "Sun"
    elif zodiac in ["Sagittarius", "Pisces"]:
        return "Jupiter"
    elif zodiac in ["Capricorn", "Aquarius"]:
        return "Saturn"

def calculate_gana(nakshatra):
    if nakshatra in ['Ashwini', 'Mrigashira', 'Punarvasu', 'Pushya', 'Hasta', 'Swati', 'Anuradha', 'Shravana', 'Revati']:
        return "Deva"
    elif nakshatra in ['Bharani', 'Rohini', 'Ardra', 'Purva Phalguni', 'Uttara Phalguni', 'Purva Ashadha', 'Uttara Ashadha', 'Purva Bhadrapada', 'Uttara Bhadrapada']:
        return "Manushya"
    elif nakshatra in ['Krittika', 'Ashlesha', 'Magha', 'Chitra', 'Visakha', 'Jyeshtha', 'Mula', 'Dhanishta', 'Shatabhisha']:
        return "Rakshasa"

def calculate_bhakoota(zodiac):
    return zodiac

def calculate_nadi(nakshatra):
    if nakshatra in ['Ashwini', 'Ardra', 'Punarvasu', 'Uttara Phalguni', 'Hasta', 'Jyeshtha', 'Mula', 'Shatabhisha', 'Purva Bhadrapada']:
        return "Adi"
    elif nakshatra in ['Bharani', 'Mrigashira', 'Pushya', 'Purva Phalguni', 'Chitra', 'Anuradha', 'Purva Ashadha', 'Dhanishta', 'Uttara Bhadrapada']:
        return "Madhya"
    else:
        return "Antya"

def generate_ashtakoota_profile(moon_zodiac, moon_deviate, nakshatra):
    varna = calculate_varna(moon_zodiac)
    # print(varna)
    vashya = calculate_vashya(moon_zodiac, moon_deviate)
    # print(vashya)
    tara = calculate_tara(nakshatra)
    # print(tara)
    yoni = calculate_yoni(nakshatra)
    # print(yoni)
    graha_maitri = calculate_graha_maitri(moon_zodiac)
    # print(graha_maitri)
    gana = calculate_gana(nakshatra)
    # print(gana)
    bhakoota = calculate_bhakoota(moon_zodiac)
    # print(bhakoota)
    nadi = calculate_nadi(nakshatra)
    # print(nadi)
    
    return AshtakootaProfile(
        moon_zodiac=moon_zodiac,
        nakshatra=nakshatra,
        varna=varna,
        vashya=vashya,
        tara=tara,
        yoni=yoni,
        graha_maitri=graha_maitri,
        gana=gana,
        bhakoota=bhakoota,
        nadi=nadi
    )

if __name__ == "__main__":
    profile = generate_ashtakoota_profile("Aries", 5, "Ashwini")
    print(profile)