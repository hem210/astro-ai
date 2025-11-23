# Running the Gradio App Locally

## Prerequisites

1. **Python 3.11+** (the project was compiled with Python 3.11.9)
2. **API Keys** for:
   - Gemini API Key (for `gemini-2.5-flash`)
   - Anthropic API Key (for `claude-sonnet-4.5`)

## Setup Steps

### 1. Install Dependencies

```bash
# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root directory:

```bash
# .env file
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
AGENT_MODEL=gemini-2.5-flash  # Optional: default model (gemini-2.5-flash or claude-sonnet-4.5)
```

**Note:** The `.env` file should be in the root directory (same level as `app.py`)

### 3. Run the Gradio App

You have two options:

#### Option A: Using `app.py` (Recommended for HuggingFace Spaces compatibility)

```bash
python app.py
```

#### Option B: Using `gradio_app.py` directly

```bash
python -m app.gradio_app
```

### 4. Access the App

Once running, you should see output like:
```
Running on local URL:  http://127.0.0.1:7860
```

Open your browser and navigate to: **http://127.0.0.1:7860**

## Troubleshooting

### Issue: "API key not found" error

**Solution:** Make sure your `.env` file is in the root directory and contains both API keys:
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

### Issue: Module not found errors

**Solution:** Make sure you've activated your virtual environment and installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Port 7860 already in use

**Solution:** Change the port in `app.py` or `gradio_app.py`:
```python
demo.launch(server_name="0.0.0.0", server_port=7861)  # Use different port
```

### Issue: Swiss Ephemeris files not found

**Solution:** Make sure the `eph` directory exists with the ephemeris files. The app expects `./eph/sepl_18.se1` to be present.

## Features

Once the app is running, you can:

1. **Enter Birth Details**: Fill in the birth details form at the top
2. **Select Model**: Choose between Gemini 2.5 Flash or Claude Sonnet 4.5
3. **Chat**: Ask questions about your astrological chart
4. **Generate Kundali**: The agent will automatically generate your chart when you ask about it

## Development Mode

For development with auto-reload, you can use:

```bash
# Install watchdog for file watching (optional)
pip install watchdog

# Run with auto-reload (requires custom setup)
python app.py
```

Note: Gradio doesn't have built-in auto-reload like FastAPI, so you'll need to restart manually when making code changes.

