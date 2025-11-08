# Political Debate Analyzer

A web application that discovers trending political topics and analyzes debates from both liberal and conservative perspectives using AI.

## Features

## Tech Stack

**Frontend:**
- React
- TypeScript
- Tailwind CSS

**Backend:**
- FastAPI (Python)
- OpenRouter API (Perplexity Sonar Pro Search)

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


### 4. Use the App

1. Open `http://localhost:3000` in your browser
2. See trending political topics displayed at the top
3. **Either**:
   - Click a trending topic to select it
   - Or enter your own custom topic
4. Click "Analyze" to get the debate analysis
5. View results with arguments from both liberal and conservative perspectives

## Project Structure

```
NovaHacks2025/
├── app.py                      # FastAPI backend API
├── search.py                   # Debate analysis logic
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create this)
├── results/                    # Saved analysis results
├── politics_news_scraper/      # News scraping & categorization
│   ├── news_scraper.py         # Fetches news from News API
│   ├── categorizer.py          # AI topic categorization
│   └── config.py               # Configuration
└── frontend/                   # React frontend
    ├── src/
    │   ├── App.tsx             # Main component
    │   └── index.css           # Tailwind CSS
    ├── tailwind.config.js      # Tailwind config
    └── package.json            # Node dependencies
```

## API Endpoints

- `GET /api/trending-topics` - Get current trending political topics
- `POST /api/analyze` - Analyze a political topic (custom or trending)
- `GET /api/health` - Health check
- Interactive API docs: `http://localhost:8000/docs`

## How It Works

1. **News Scraping**: Fetches recent political articles from News API
2. **Topic Generation**: Uses Claude 3.5 Sonnet via OpenRouter to identify trending topics
3. **User Selection**: User chooses a trending topic or enters their own
4. **Debate Analysis**: Perplexity Sonar Pro analyzes the topic and generates arguments from both sides
5. **Results Display**: Shows comprehensive debate analysis with sources

## Security Note

Never commit your `.env` file or expose your API keys. The `.gitignore` is configured to exclude sensitive files.
