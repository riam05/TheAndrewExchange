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
python3 -m uvicorn app:app --reload
```


### 3. Open New Terminal (Terminal 2)


### 4. Frontend Command:


```bash
npm start
```



### 5. Use the App

1. Open in your browser
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