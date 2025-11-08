# The Andrew Exchange

A web application that discovers trending political topics, analyzes debates from both liberal (Andrew Carnegie) and conservative (Andrew Mellon) perspectives, generates debate scripts, and creates AI-powered audio with distinct voices for each side.

## Tech Stack

**Frontend:**
- React
- TypeScript
- Tailwind CSS

**Backend:**
- FastAPI (Python)
- OpenRouter API (Perplexity Sonar Pro Search for debate analysis, GPT-4o for script generation)
- Eleven Labs API (AI Text-to-Speech for audio generation)

## Quick Start Guide


### 1. Open New Terminal (Terminal 1)


### 2. Backend Command:


```bash
cd /Users/riamehta/Documents/GitHub/NovaHacks2025
python3 -m uvicorn app:app --reload
```


The backend will start on `http://localhost:8000`


### 3. Open New Terminal (Terminal 2)


### 4. Frontend Command:


```bash
cd /Users/riamehta/Documents/GitHub/NovaHacks2025/frontend
npm start
```


The frontend will start on `http://localhost:3000` and automatically open in your browser.


### 5. Use the App

1. Open `http://localhost:3000` in your browser
2. See trending political topics displayed at the top
3. **Either**:
   - Click a trending topic to select it
   - Or enter your own custom topic
4. Click "Analyze" - this will:
   - Generate debate arguments (liberal vs conservative)
   - Create a conversational script between Carnegie (liberal) and Mellon (conservative)
   - Generate audio files with distinct AI voices for each speaker
5. Listen to the debate by clicking "Play Debate"
6. Watch the speaker portraits animate as each side speaks

## How It Works

The app runs a complete AI pipeline when you analyze a topic:

1. **Trending Topics** → News API fetches recent political articles → AI categorizes them into trending topics
2. **Topic Analysis** → Perplexity Sonar Pro Search analyzes both sides of the debate with recent sources
3. **Script Generation** → GPT-4o creates a natural conversation script between Carnegie (liberal) and Mellon (conservative)
4. **Audio Generation** → Eleven Labs converts each speaker's lines into audio with distinct voices
5. **Playback** → Frontend plays the audio files in sequence with visual indicators

## Project Structure

```
NovaHacks2025/
├── app.py                      # FastAPI backend API (main server)
├── search.py                   # Debate analysis logic
├── script_generator.py         # AI script generation
├── videogenerator.py           # Audio generation with Eleven Labs
├── requirements.txt            # Python dependencies
├── .env                        # API keys (OPENROUTER_API_KEY, ELEVENLABS_API_KEY, NEWS_API_KEY)
├── results/                    # Saved debate JSON files
├── audio_output/               # Generated audio files for debates
├── politics_news_scraper/      # News scraping & categorization
│   ├── news_scraper.py         # Fetches news from News API
│   ├── categorizer.py          # AI topic categorization
│   └── config.py               # Configuration
└── frontend/                   # React frontend
    ├── src/
    │   ├── App.tsx             # Main component with audio player
    │   └── index.css           # Tailwind CSS
    ├── public/
    │   ├── carnegie.jpg        # Portrait of Andrew Carnegie (liberal)
    │   └── mellon.jpg          # Portrait of Andrew Mellon (conservative)
    ├── tailwind.config.js      # Tailwind config
    └── package.json            # Node dependencies
```

## API Endpoints

- `GET /api/trending-topics` - Get current trending political topics (from news)
- `POST /api/analyze` - **Full Pipeline**: Analyze topic → Generate script → Create audio files
- `GET /api/audio-files` - List all generated audio files
- `GET /audio/{filename}` - Stream/download specific audio file
- `GET /api/health` - Health check
- Interactive API docs: `http://localhost:8000/docs`

## Environment Variables

Create a `.env` file in the root directory with:

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
NEWS_API_KEY=your_news_api_key_here

# Optional: Custom voice IDs for Eleven Labs
ELEVENLABS_CARNEGIE_VOICE_ID=pNInz6obpgDQGcFmaJgB  # Default: Adam
ELEVENLABS_MELLON_VOICE_ID=VR6AewLTigWG4xSOukaG   # Default: Arnold
```

To list available Eleven Labs voices, run:
```bash
python videogenerator.py --list-voices
```

## Security Note

Never commit your `.env` file or expose your API keys. The `.gitignore` is configured to exclude sensitive files.
