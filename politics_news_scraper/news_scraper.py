"""
News scraper module for fetching recent politics-related articles.
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from .config import NEWS_API_KEY, NEWS_API_BASE_URL, ARTICLES_PER_CATEGORY, OPENROUTER_API_KEY, OPENROUTER_BASE_URL, CATEGORIZATION_MODEL


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
        
        # Try different search queries for the /everything endpoint
        queries = [
            {"q": "politics", "language": "en"},
            {"q": "political", "language": "en"},
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
    
    def filter_foreign_local_politics(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter out articles about foreign local politics that aren't international affairs.
        Uses batching to check multiple articles at once for efficiency.
        
        Args:
            articles: List of article dictionaries
        
        Returns:
            Filtered list of articles
        """
        print("🌍 Filtering foreign local politics articles...")
        
        if not OPENROUTER_API_KEY:
            # If no API key, skip filtering
            return articles
        
        # Batch articles for efficiency (check 10 at a time)
        batch_size = 10
        filtered = []
        removed_count = 0
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            batch_results = self._check_batch_foreign_local_politics(batch)
            
            for article, should_remove in zip(batch, batch_results):
                if not should_remove:
                    filtered.append(article)
                else:
                    removed_count += 1
        
        if removed_count > 0:
            print(f"   Removed {removed_count} foreign local politics articles")
        
        return filtered
    
    def _check_batch_foreign_local_politics(self, articles: List[Dict]) -> List[bool]:
        """
        Check a batch of articles for foreign local politics in a single API call.
        
        Args:
            articles: List of article dictionaries to check
        
        Returns:
            List of booleans, True if article should be filtered out
        """
        if not OPENROUTER_API_KEY:
            return [False] * len(articles)
        
        # Create article summaries
        articles_text = "\n\n".join([
            f"Article {i+1}:\nTitle: {article.get('title', '')}\nDescription: {article.get('description', '')}\nContent: {article.get('content', '')[:200] if article.get('content') else ''}"
            for i, article in enumerate(articles)
        ])
        
        prompt = f"""You are analyzing news articles to determine if they should be filtered out.

Articles:
{articles_text}

For each article, determine if it is about LOCAL POLITICS in a FOREIGN COUNTRY that is NOT directly related to international affairs or US politics.

Examples of articles to FILTER OUT (return true):
- Local elections in Hungary, Poland, or other foreign countries
- Local political opposition movements in foreign countries
- Municipal politics in foreign cities
- Regional politics in foreign countries

Examples of articles to KEEP (return false):
- International relations between countries
- US foreign policy
- Global political events affecting multiple countries
- US politics (domestic or international)
- Major international conflicts or crises
- Trade agreements between countries

Return a JSON array of booleans, one for each article in order (true = filter out, false = keep).
Example format: [false, true, false, false, ...]

Return ONLY the JSON array, nothing else."""
        
        try:
            url = f"{OPENROUTER_BASE_URL}/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": CATEGORIZATION_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that analyzes news articles. Always respond with only a valid JSON array of booleans."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            result_text = data["choices"][0]["message"]["content"].strip()
            
            # Clean response
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()
            
            import json
            results = json.loads(result_text)
            
            # Ensure we have the right number of results
            if isinstance(results, list) and len(results) == len(articles):
                return results
            else:
                # Fallback: assume all should be kept
                print(f"Warning: Unexpected batch result format, keeping all articles")
                return [False] * len(articles)
        except Exception as e:
            # On error, don't filter (safer to include than exclude)
            print(f"Warning: Error checking batch for foreign local politics: {e}")
            return [False] * len(articles)

