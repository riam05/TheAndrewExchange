"""
Dynamic categorizer module using OpenRouter API for categorizing politics articles.
"""
import requests
import json
from typing import List, Dict, Set
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, CATEGORIZATION_MODEL


class DynamicCategorizer:
    """Categorizer that dynamically generates categories and assigns articles."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY in .env file.")
        self.base_url = OPENROUTER_BASE_URL
    
    def _call_openrouter(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """
        Make a call to OpenRouter API.
        
        Args:
            messages: List of message dictionaries for the chat
            temperature: Temperature for the model
        
        Returns:
            Response text from the model
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Optional: for tracking
        }
        
        payload = {
            "model": CATEGORIZATION_MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling OpenRouter API: {e}")
    
    def generate_categories(self, article_summaries: List[str], num_categories: int = None) -> List[str]:
        """
        Dynamically generate categories based on article content.
        
        Args:
            article_summaries: List of article summary strings
            num_categories: Desired number of categories (None for automatic)
        
        Returns:
            List of category names
        """
        # Create a summary of all articles
        articles_text = "\n\n".join([f"Article {i+1}:\n{summary}" for i, summary in enumerate(article_summaries[:20])])
        
        num_categories_prompt = f"Generate approximately {num_categories} categories" if num_categories else "Generate an appropriate number of categories"
        
        prompt = f"""You are analyzing recent politics-related news articles. Based on the following articles, {num_categories_prompt} that best organize these articles.

Articles:
{articles_text}

Please:
1. Identify the main themes and topics
2. Create clear, descriptive category names (e.g., "Election Coverage", "Foreign Policy", "Legislative Updates", "Political Scandals")
3. Return ONLY a JSON array of category names, nothing else

Example format: ["Category 1", "Category 2", "Category 3"]
"""
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that analyzes news articles and creates logical categories. Always respond with valid JSON arrays."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self._call_openrouter(messages, temperature=0.5)
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code blocks
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            categories = json.loads(response)
            if isinstance(categories, list):
                return [str(cat) for cat in categories]
            else:
                raise ValueError("Response is not a list")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing categories, using fallback: {e}")
            # Fallback categories
            return ["General Politics", "Elections", "Policy", "International Relations", "Domestic Affairs"]
    
    def categorize_articles(self, articles: List[Dict], categories: List[str]) -> Dict[str, List[Dict]]:
        """
        Categorize articles into the provided categories.
        
        Args:
            articles: List of article dictionaries
            categories: List of category names
        
        Returns:
            Dictionary mapping category names to lists of articles
        """
        categorized = {category: [] for category in categories}
        
        # Process articles in batches for efficiency
        batch_size = 10
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            
            # Create prompt for batch
            articles_text = "\n\n".join([
                f"Article {j+1}:\nTitle: {article.get('title', 'No title')}\nDescription: {article.get('description', 'No description')[:300]}"
                for j, article in enumerate(batch)
            ])
            
            prompt = f"""You are categorizing politics news articles. For each article below, assign it to ONE of these categories:

Categories: {', '.join(categories)}

Articles:
{articles_text}

For each article, return a JSON object mapping article numbers to category names.
Example format: {{"1": "Category Name", "2": "Category Name", ...}}

Return ONLY the JSON object, nothing else."""
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that categorizes news articles. Always respond with valid JSON objects."},
                {"role": "user", "content": prompt}
            ]
            
            try:
                response = self._call_openrouter(messages, temperature=0.3)
                # Clean response
                response = response.strip()
                if response.startswith("```"):
                    response = response.split("```")[1]
                    if response.startswith("json"):
                        response = response[4:]
                response = response.strip()
                
                assignments = json.loads(response)
                
                # Assign articles to categories
                for j, article in enumerate(batch):
                    article_num = str(j + 1)
                    if article_num in assignments:
                        category = assignments[article_num]
                        if category in categorized:
                            categorized[category].append(article)
                        else:
                            # Fallback to first category if category not found
                            categorized[categories[0]].append(article)
                    else:
                        # Fallback to first category
                        categorized[categories[0]].append(article)
                        
            except (json.JSONDecodeError, ValueError, Exception) as e:
                print(f"Error categorizing batch {i//batch_size + 1}: {e}")
                # Fallback: assign to first category
                for article in batch:
                    categorized[categories[0]].append(article)
        
        return categorized

