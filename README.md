# Political Debate Analyzer

A web application that discovers trending political topics and analyzes debates from both liberal and conservative perspectives using AI.

## Features

- 🔥 **Trending Topics**: Automatically fetches and displays current political topics from news
- 🎨 **Beautiful UI**: Modern landing page built with React, TypeScript, and Tailwind CSS
- 🔍 **AI-Powered Analysis**: Uses Perplexity's Sonar Pro Search for real-time debate analysis
- 📊 **Balanced Perspectives**: Presents both liberal and conservative viewpoints with sources
- 🔐 **Secure**: Environment variable management for API keys

## Tech Stack

**Frontend:**
- React
- TypeScript
- Tailwind CSS

**Backend:**
- FastAPI (Python)
- OpenRouter API (Perplexity Sonar Pro Search)

## Setup Instructions

### 1. Install Dependencies

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:
```
OPENROUTER_API_KEY=your_api_key_here
NEWS_API_KEY=your_news_api_key_here  # Optional: for trending topics (get from https://newsapi.org)
```

**Note:** NEWS_API_KEY is optional. If not provided, the app will use fallback trending topics.

### 3. Run the Application

**Terminal 1 - Start Backend:**
```bash
uvicorn app:app --reload
```
Backend will run on `http://localhost:8000`

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm start
```
Frontend will run on `http://localhost:3000`

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
├── app.py                 # FastAPI backend API
├── search.py             # Original search script
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── results/              # Saved analysis results
└── frontend/             # React frontend
    ├── src/
    │   ├── App.tsx       # Main landing page component
    │   └── index.css     # Tailwind CSS
    └── package.json      # Node dependencies
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
