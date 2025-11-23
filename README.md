# Astro-AI

## Overview

Astro-AI is an intelligent Vedic astrology chatbot platform that combines traditional astrological calculations with modern AI-powered natural language understanding. The system uses an agentic RAG (Retrieval-Augmented Generation) architecture built with LangGraph to provide personalized astrological readings through conversational interactions.

The platform features a FastAPI backend with REST API endpoints for programmatic access, and a Gradio-based conversational interface for interactive consultations. It leverages Swiss Ephemeris for accurate planetary calculations and maintains a comprehensive knowledge base of Vedic astrology interpretations, enabling the AI agent to provide contextually relevant and personalized insights.

## Screenshots

### Gradio App

1. Birth Details Form
![alt text](app/docs_assets/gradio_birth_info_input.png)

2. Chat Interface
![alt text](app/docs_assets/gradio_chat_interface.png)

## Installing and Running Locally

You can also run the Gradio app locally by following the instructions in [RUN_GRADIO.md](RUN_GRADIO.md).

Run the following commands in your terminal to set things up. By default the backend will be running at: http://127.0.0.1:8000. This is the older version of the API endpoints.

Also, this application was compiled with Python v3.11.9. So any version equal or above it will be fine.
```
git clone https://github.com/hem210/astro-ai.git
cd astro-ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.api.main:app --reload
```

## Features & Capabilities

- **Vedic Astrology Calculations**: Uses the Swiss Ephemeris (with Lahiri sidereal system) for accurate planetary and house computations aligned with traditional Indian astrology.

- **Kundali Generation**: Computes detailed natal charts, including ascendants and planetary positions across houses.

- **Agentic RAG System**: Built with LangGraph for multi-step reasoning and tool orchestration. The agent autonomously retrieves relevant astrological interpretations from a comprehensive knowledge base (291 entries covering planet-house, planet-sign, ascendant, nakshatra, and conjunction combinations) and synthesizes them into personalized readings.

- **Tool-Based Agent Architecture**: Implements a conversational AI agent that uses tools to generate charts and query the knowledge base, making intelligent decisions about when and what to retrieve based on user queries.

- **Multi-LLM Support**: Supports multiple language models (Gemini, Claude) via LiteLLM, allowing flexible model selection and load balancing.

- **Structured Knowledge Retrieval**: Maps natural language queries to structured astrological concepts, enabling precise context retrieval from the knowledge base without requiring semantic search.

- **Conversational Interface**: Gradio-based chat interface for interactive astrology consultations with conversation history and context awareness.

- **Matchmaking Logic**: Implements classical Ashtakoota matching with an 8-dimension scoring system for compatibility.

- **LLM-Based Explanation**: Uses language models to explain Ashtakoota scores in plain language, making astrological insights accessible to non-experts.

- **Personalized Match Suggestions**: Recommends compatible Rashi-Nakshatra pairs along with the Name letters for individuals based on traditional compatibility rules. This helps in easy identification of people based on names for compatibility (assuming people are named based on the appropriate letters of Rashi/Nakshatra).

## API Endpoints (Older Version)

1. `/kundali`: Generates a detailed Kundali (natal chart), including planetary positions and house placements, based on date, time, and place of birth.

2. `/ashtakoota-score`: Computes the Ashtakoota score for two individuals, covering all 8 compatibility dimensions used in Vedic matchmaking.

3. `/my-perfect-match`: Returns top compatible Rashi-Nakshatra-NameLetters with score > 22 (which is deemed compatible as per Vedic astrology) for an individual, based on traditional Indian matchmaking principles.

4. `/ashtakoota-score-explain` (LLM-enhaced): Uses LLM Agents to provide a natural language explanation of the Ashtakoota score — breaking down how each dimension contributes and what it means for a relationship. This is the core feature aimed at demystifying traditional astrology.

### Screenshots (Older Version)

1. `/kundali`
![alt text](app/docs_assets/kundali_api_response.png)

2. `/ashtakoota-score`
![alt text](app/docs_assets/ashtakoota_score_api_response.png)

3. `/my-perfect-match`
![alt text](app/docs_assets/my_perfect_match_api_response.png)

4. `/ashtakoota-score-explain`
![alt text](app/docs_assets/ashtakoota_score_explain_api_response.png)