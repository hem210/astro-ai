
def generate_ashtakoota_explanation(ashtakoota_score_data: str, groom_moon_zodiac: str, groom_nakshatra: str, bride_moon_zodiac: str, bride_nakshatra: str) -> str:
    ashtakoota_explanation_prompt = f"""
You are an expert Indian astrologer specializing in matchmaking interpretations.

Given the following compatibility data between two individuals:
- Their Rashi (Moon sign) and Nakshatra (Birth star)
- The Gun Milan scores across 8 dimensions (Varna, Vashya, Tara, Yoni, Graha Maitri, Gana, Bhakoot, Nadi)

Your task is to explain each of the 8 dimensions (kootas) clearly. For each koota:
1. Describe what this koota represents in relationship compatibility
2. State the score out of its maximum (e.g., 4/4)
3. Interpret what their score implies for the relationship
4. Mention any positive aspects or cautions based on the score

Input Data:
Groom Rashi (Moon Sign): {groom_moon_zodiac}
Groom Nakshatra: {groom_nakshatra}
Bride Rashi (Moon Sign): {bride_moon_zodiac}
Bride Nakshatra: {bride_nakshatra}

Ashtakoota Score Data:
{ashtakoota_score_data}

Output Format:
Varna Matching (Score X/Y):  
[Explanation]  

Vashya Matching (Score X/Y):  
[Explanation]  

...(repeat for all 8)

Important: Be concise (2-3 sentences per koota), accurate to traditional astrological principles, and avoid exaggerations.
"""
    return ashtakoota_explanation_prompt

def generate_ashtakoota_summary(ashtakoota_explanation: str, total_score: float) -> str:
    ashtakoota_summary_prompt = f"""
You are an expert Indian astrologer skilled in summarizing matchmaking compatibility insights.

Given the following detailed explanations of the 8 Gun Milan kootas and the total compatibility score, generate:
1. A brief summary of the overall relationship potential (1 paragraph)
2. Key strengths and cautions (bullet points)
3. A general advice on marriage suitability

Input Explanations:
{ashtakoota_explanation}

Total Score: {total_score} / 36

Important: Your output should be neutral and culturally sensitive. Do not give absolute judgments; instead, highlight strengths and gently mention areas of caution.
"""
    return ashtakoota_summary_prompt
