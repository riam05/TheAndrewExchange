"""
News scraper module for fetching recent politics-related articles.
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .config import NEWS_API_KEY, NEWS_API_BASE_URL, ARTICLES_PER_CATEGORY


class NewsScraper:
    """Scraper for fetching politics-related news articles."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or NEWS_API_KEY
        if not self.api_key:
            print("Warning: News API key not set. Trending topics may use fallback values.")
    
    def fetch_recent_politics_articles(self, days_back: int = 7, max_articles: int = None) -> List[Dict]:
        """
        Fetch recent politics-related articles from News API.
        
        Args:
            days_back: Number of days to look back for articles
            max_articles: Maximum number of articles to fetch (None for default)
        
        Returns:
            List of article dictionaries
        """
        max_articles = max_articles or ARTICLES_PER_CATEGORY * 5  # Fetch more for categorization
        
        # Calculate date range
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        articles = []
        
        # Try different endpoints and queries
        queries = [
            {"q": "politics", "language": "en"},
            {"q": "political", "language": "en"},
            {"category": "politics", "language": "en"},
        ]
        
        for query_params in queries:
            if len(articles) >= max_articles:
                break
                
            try:
                # Try everything endpoint first
                url = f"{NEWS_API_BASE_URL}/everything"
                params = {
                    **query_params,
                    "apiKey": self.api_key,
                    "sortBy": "publishedAt",
                    "pageSize": min(100, max_articles - len(articles)),
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if data.get("status") == "ok":
                    new_articles = data.get("articles", [])
                    # Deduplicate by URL
                    existing_urls = {article.get("url") for article in articles}
                    for article in new_articles:
                        if article.get("url") and article.get("url") not in existing_urls:
                            articles.append(article)
                            existing_urls.add(article.get("url"))
                            
            except requests.exceptions.RequestException as e:
                print(f"Error fetching articles with query {query_params}: {e}")
                continue
        
        # If we still don't have enough, try top headlines
        if len(articles) < max_articles:
            try:
                url = f"{NEWS_API_BASE_URL}/top-headlines"
                params = {
                    "category": "politics",
                    "language": "en",
                    "apiKey": self.api_key,
                    "pageSize": min(100, max_articles - len(articles)),
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                if data.get("status") == "ok":
                    new_articles = data.get("articles", [])
                    existing_urls = {article.get("url") for article in articles}
                    for article in new_articles:
                        if article.get("url") and article.get("url") not in existing_urls:
                            articles.append(article)
                            existing_urls.add(article.get("url"))
            except requests.exceptions.RequestException as e:
                print(f"Error fetching top headlines: {e}")
        
        return articles[:max_articles]
    
    def format_article_for_categorization(self, article: Dict) -> str:
        """
        Format article into a string for categorization.
        
        Args:
            article: Article dictionary from News API
        
        Returns:
            Formatted string with article information
        """
        title = article.get("title", "No title")
        description = article.get("description", "")
        content = article.get("content", "")
        
        # Use content if available, otherwise description
        body = content[:500] if content else description[:500]
        
        return f"Title: {title}\nDescription: {body}"

