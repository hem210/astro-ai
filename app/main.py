import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import kundali, matchmaking
from app.routes import auth, profile, conversations, compatibility

app = FastAPI(title="Astro AI")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# In production, set FRONTEND_ORIGIN to your actual frontend URL.
# During development, localhost:5173 is the Vite default.

_frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_origin],
    allow_credentials=True,   # required for cookies (refresh token)
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(kundali.router)
app.include_router(matchmaking.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(conversations.router)
app.include_router(compatibility.router)


@app.get("/")
async def read_root():
    return {"status": "ok"}
