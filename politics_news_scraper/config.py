"""
Configuration file for the politics news scraper and categorizer.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# News API Configuration
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_BASE_URL = "https://newsapi.org/v2"

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Scraping Configuration
ARTICLES_PER_CATEGORY = 20  # Number of articles to fetch
CATEGORIZATION_MODEL = "anthropic/claude-3.5-sonnet"  # Model for categorization

