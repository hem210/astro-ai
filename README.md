# Astro AI

A full-stack Vedic astrology web application. It calculates natal charts, divisional charts, and matchmaking compatibility using Swiss Ephemeris, and provides an AI chat interface backed by a Vedic knowledge base.

## What it does

The app is built around a logged-in user who has a birth profile. From that profile it computes their Kundali and lets them:

- **Chat with an AI astrologer** — a LangGraph agent that calls tools to generate the natal chart, query a curated Vedic knowledge base, compute Vimshottari dasha periods, and pull divisional charts (D9/D10/D12) depending on the question. Career questions get the Dashamsha, marriage questions get the Navamsa.
- **Run partner compatibility** — add a partner's birth details, get an Ashtakoota score (0–36) across all 8 kootas, Mangal Dosha analysis with cancellation detection, and a streaming AI explanation of what the scores mean together.
- **Find best matches** — sweeps all 36 Rashi-Nakshatra combinations, scores each against the user's profile, surfaces Nadi and Bhakoota doshas with cancellation logic, and shows the name syllables (namakarana aksharas) for each candidate.

## Vedic calculations

All planetary positions use **Swiss Ephemeris** (`pyswisseph`) with the **Lahiri ayanamsa** (sidereal). Whole sign house system.

**Divisional charts** — all derived from D1 longitudes using classical Parashari rules:
- D9 (Navamsa): element-based starting sign — fire→Aries, earth→Capricorn, air→Libra, water→Cancer; 9 padas of 3°20'
- D10 (Dashamsha): odd signs start from themselves, even signs from the 9th sign; 10 padas of 3°
- D12 (Dvadashamsha): every sign starts from itself; 12 padas of 2°30'

**Ashtakoota matching** — all 8 kootas scored: Varna (1), Vashya (2), Tara (3), Yoni (4), Graha Maitri (5), Gana (6), Bhakoota (7), Nadi (8). Max 36.

**Dosha detection with cancellation:**
- Nadi dosha cancelled when same Rashi + different Nakshatra, or same Nakshatra + different Rashi
- Bhakoota dosha cancelled when Graha Maitri score is full (5/5)
- Mangal dosha checked for both partners with severity (high/medium/mild) and classical cancellation conditions

**Vimshottari dasha** — computed from Moon's nakshatra longitude; supports querying arbitrary date ranges for mahadasha/antardasha breakdown.

## Tech stack

- **Backend**: FastAPI, SQLAlchemy, Alembic, PostgreSQL, Argon2, JWT (access + refresh tokens), SlowAPI
- **Frontend**: React, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, React Router
- **AI**: LangGraph, LiteLLM (Gemini 2.5 Flash / Claude Sonnet), streaming SSE
- **Astrology**: pyswisseph, geopy

## Running locally

### Backend

Requires Python 3.11+, PostgreSQL, and [`uv`](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/hem210/astro-ai.git
cd astro-ai

cp .env.example .env
# fill in DATABASE_URL, GEMINI_API_KEY or ANTHROPIC_API_KEY, JWT_SECRET_KEY

uv sync
alembic upgrade head
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`.

### Frontend

Requires Node 18+.

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Project structure

```
app/
  routes/          # FastAPI route handlers (auth, chat, compatibility, best-matches, …)
  services/
    agent/         # LangGraph agent — graph, tools, system prompt
    ashtakoota_services/   # Koota scoring and profile generation
    kundali_chart.py       # D1 + D9/D10/D12 calculations via swisseph
    match_finder.py        # Best-matches sweep with dosha detection
    vimshottari.py         # Dasha period computation
  db/              # SQLAlchemy models and session
  core/            # Auth, quota, rate limiting
  data/            # vedic_knowledge_base.json

frontend/
  src/
    pages/         # ChatPage, PartnersPage, MatchesPage, OnboardingPage, …
    components/    # shadcn/ui components
    api/           # Axios client + SSE fetch helper

alembic/           # DB migrations
scripts/           # Standalone chart verification scripts (D9, knowledge base generation)
eph/               # Swiss Ephemeris data files (not tracked in git)
```
