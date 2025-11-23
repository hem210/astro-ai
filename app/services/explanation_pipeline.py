from app.models import AshtakootaMatchScore, AshtakootaProfile
from app.services.prompt_service import generate_ashtakoota_explanation, generate_ashtakoota_summary
from app.services.gemini_service import call_gemini

async def ashtakoota_explanation_pipeline(ashtakoota_match_score: AshtakootaMatchScore, groom_profile: AshtakootaProfile, bride_profile: AshtakootaProfile):
    final_response = ""
    
    exp_prompt = generate_ashtakoota_explanation(ashtakoota_match_score.model_dump_json(indent=2), groom_profile.moon_zodiac, groom_profile.nakshatra, bride_profile.moon_zodiac, bride_profile.nakshatra)
    exp_response = await call_gemini(exp_prompt)
    final_response += exp_response + "\n\n"

    sum_prompt = generate_ashtakoota_summary(exp_response, ashtakoota_match_score.total)
    sum_response = await call_gemini(sum_prompt)
    final_response += sum_response

    return final_response
