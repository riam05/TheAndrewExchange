# Politics News Scraper & Dynamic Categorizer

A query-less scraping system that automatically finds recent politics-related news articles, dynamically generates categories based on content, and organizes articles into these categories.

## Features

- 🔍 **Automatic Article Discovery**: Fetches recent politics articles from News API without manual queries
- 🧠 **Dynamic Categorization**: Uses OpenRouter API (Claude 3.5 Sonnet) to generate categories based on article content
- 📊 **Smart Organization**: Automatically assigns articles to the most relevant generated categories
- 📁 **Multiple Output Formats**: Console display and JSON export

## Prerequisites

- Python 3.8+
- News API key ([get one here](https://newsapi.org/))
- OpenRouter API key ([get one here](https://openrouter.ai/))

## Setup

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys**:
   - Copy `.env.example` to `.env`
   - Add your API keys:
     ```
     NEWS_API_KEY=your_news_api_key_here
     OPENROUTER_API_KEY=your_openrouter_api_key_here
     ```

## Usage

Run the main script:

```bash
python main.py
```

The script will:
1. Fetch recent politics articles (last 7 days)
2. Analyze articles to generate relevant categories
3. Categorize all articles into the generated categories
4. Display results in the console
5. Save results to a JSON file

## How It Works

### 1. Article Scraping (`news_scraper.py`)
- Queries News API for recent politics articles
- Uses multiple search strategies to maximize article discovery
- Filters and deduplicates results

### 2. Dynamic Categorization (`categorizer.py`)
- Uses OpenRouter API to access Claude 3.5 Sonnet
- Analyzes article content to identify themes
- Generates appropriate category names
- Assigns each article to the most relevant category

### 3. Output (`main.py`)
- Displays categorized articles in a readable console format
- Exports results to timestamped JSON files

## Configuration

Edit `config.py` to customize:
- Number of articles to fetch
- LLM model for categorization (default: `anthropic/claude-3.5-sonnet`)
- Date range for article fetching

## Output Format

### Console Output
Shows articles organized by category with:
- Article titles
- Sources
- Publication dates
- Descriptions
- URLs

### JSON Output
Saves to `categorized_articles_YYYYMMDD_HHMMSS.json` with structured data:
```json
{
  "generated_at": "2024-01-15T10:30:00",
  "categories": {
    "Election Coverage": [...],
    "Foreign Policy": [...],
    ...
  }
}
```

## Notes

- **News API Free Tier**: Limited to 100 requests/day. For production use, consider upgrading.
- **OpenRouter**: Pay-per-use pricing. Check [OpenRouter pricing](https://openrouter.ai/docs/pricing) for details.
- **Webhooks**: Not required for this implementation. The system runs on-demand when executed.

## Troubleshooting

- **No articles found**: Check your News API key and internet connection
- **Categorization errors**: Verify your OpenRouter API key and account balance
- **Rate limiting**: News API free tier has limits; wait or upgrade your plan

## License

MIT License - feel free to modify and use as needed.

