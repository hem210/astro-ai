import httpx
import asyncio
from app.config import API_URL


headers = {
    "Content-Type": "application/json"
}

async def call_gemini(prompt):
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(API_URL, headers=headers, json=data)
            if response.status_code == 200:
                output = response.json()
                return output["candidates"][0]["content"]["parts"][0]["text"]
            else:
                return f"Error {response.status_code}: {response.text}"
        except httpx.RequestError as e:
            return f"Request error: {e}"


if __name__ == "__main__":
    prompt = "Explain the Graha Maitri koota when the score is 4 out of 5 in a marriage match."
    result = asyncio.run(call_gemini(prompt))
    print(result)