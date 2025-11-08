"""
Dynamic categorizer module using OpenRouter API for categorizing politics articles.
"""
import requests
import json
from typing import List, Dict, Set, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, CATEGORIZATION_MODEL


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
            2. Create clear, SPECIFIC category names (e.g., "Trump Tariffs", "Decreasing Housing Cost", "SNAP Payments")
            3. It is encouraged to include relevant names of people, organizations, or policies, but make sure to be specific.
            4. Return ONLY a JSON array of category names, nothing else

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
        Also filters out foreign local politics articles during categorization.
        
        Args:
            articles: List of article dictionaries
            categories: List of category names
        
        Returns:
            Dictionary mapping category names to lists of articles
        """
        categorized = {category: [] for category in categories}
        filtered_count = 0
        
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

                IMPORTANT FILTERING RULE:
                - If an article is about LOCAL POLITICS in a FOREIGN COUNTRY that is NOT directly related to international affairs or US politics, assign it to "FILTER_OUT" instead of a category.
                - Examples to FILTER_OUT: Local elections in Hungary/Poland/other foreign countries, local political opposition movements in foreign countries, municipal politics in foreign cities, regional politics in foreign countries.
                - Examples to KEEP: International relations, US foreign policy, global political events, US politics, major international conflicts, trade agreements.

                Articles:
                {articles_text}

                For each article, return a JSON object mapping article numbers to category names (or "FILTER_OUT").
                Example format: {{"1": "Category Name", "2": "FILTER_OUT", "3": "Category Name", ...}}

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
                
                # Assign articles to categories (filter out "FILTER_OUT" articles)
                for j, article in enumerate(batch):
                    article_num = str(j + 1)
                    if article_num in assignments:
                        category = assignments[article_num]
                        if category == "FILTER_OUT":
                            # Skip foreign local politics articles
                            filtered_count += 1
                            continue
                        elif category in categorized:
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
        
        if filtered_count > 0:
            print(f"   Filtered out {filtered_count} foreign local politics articles during categorization")
        
        return categorized
    
    def check_category_relevance(self, category: str, articles: List[Dict]) -> bool:
        """
        Check if articles in a category are actually on-topic for that category.
        
        Args:
            category: Category name
            articles: List of articles in this category
        
        Returns:
            True if articles are relevant to the category, False otherwise
        """
        if len(articles) == 0:
            return False
        
        # Create summary of articles
        articles_text = "\n\n".join([
            f"Article {i+1}:\nTitle: {article.get('title', 'No title')}\nDescription: {article.get('description', 'No description')[:200]}"
            for i, article in enumerate(articles)
        ])
        
        prompt = f"""You are analyzing whether articles are actually on-topic for their assigned category.

Category: "{category}"

Articles assigned to this category:
{articles_text}

Determine if these articles are actually relevant and on-topic for the category "{category}".

Return "true" if at least 2 articles are clearly relevant to the category.
Return "false" if the articles are not relevant, too niche, or the category doesn't make sense for these articles.

Return ONLY "true" or "false" (lowercase, no quotes, no explanation)."""
        
        try:
            response = self._call_openrouter([
                {"role": "system", "content": "You are a helpful assistant that analyzes article-category relevance. Always respond with only 'true' or 'false'."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            result = response.strip().lower()
            return result == "true"
        except Exception as e:
            print(f"Warning: Error checking category relevance: {e}")
            # On error, assume relevant (safer to keep than remove)
            return True
    
    def filter_and_validate_categories(self, categorized_articles: Dict[str, List[Dict]], 
                                       article_summaries: List[str], 
                                       all_articles: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Filter categories to remove those with < 2 articles or low relevance.
        Regenerate categories if needed.
        
        Args:
            categorized_articles: Dictionary mapping categories to article lists
            article_summaries: List of article summaries for regeneration
            all_articles: All articles (for recategorization if needed)
        
        Returns:
            Filtered dictionary of categorized articles
        """
        print("\n🔍 Validating categories...")
        
        # Step 1: Remove categories with < 2 articles
        valid_categories = {}
        removed_small = []
        
        for category, articles in categorized_articles.items():
            if len(articles) >= 2:
                valid_categories[category] = articles
            else:
                removed_small.append(category)
                print(f"   Removed '{category}' (only {len(articles)} article(s))")
        
        if removed_small:
            print(f"   Removed {len(removed_small)} categories with < 2 articles")
        
        # Step 2: Check relevance of remaining categories (batched for efficiency)
        relevant_categories = {}
        removed_irrelevant = []
        
        # Batch validate categories (check multiple at once)
        categories_to_check = list(valid_categories.items())
        batch_size = 5  # Check 5 categories at a time
        
        for i in range(0, len(categories_to_check), batch_size):
            batch = categories_to_check[i:i+batch_size]
            batch_results = self._check_batch_category_relevance(batch)
            
            for (category, articles), is_relevant in zip(batch, batch_results):
                if is_relevant:
                    relevant_categories[category] = articles
                else:
                    removed_irrelevant.append(category)
                    print(f"   Removed '{category}' (articles not on-topic)")
        
        if removed_irrelevant:
            print(f"   Removed {len(removed_irrelevant)} categories with low relevance")
        
        # Step 3: Collect articles from removed categories for recategorization
        removed_articles = []
        for category in removed_small + removed_irrelevant:
            removed_articles.extend(categorized_articles.get(category, []))
        
        # Step 4: Recategorize orphaned articles AND rename all categories (renaming in last batch call)
        if removed_articles and relevant_categories:
            print(f"\n📋 Recategorizing {len(removed_articles)} articles and renaming categories...")
            existing_categories = list(relevant_categories.keys())
            
            # Batch recategorization for efficiency (process 5 at a time)
            batch_size = 5
            total_batches = (len(removed_articles) + batch_size - 1) // batch_size
            
            for i in range(0, len(removed_articles), batch_size):
                batch = removed_articles[i:i+batch_size]
                is_last_batch = (i // batch_size + 1) == total_batches
                
                if is_last_batch:
                    # Last batch: recategorize AND rename categories in one call
                    batch_assignments, renamed_categories, name_mapping = self._recategorize_and_rename_combined(
                        batch, existing_categories, relevant_categories
                    )
                    
                    # Apply recategorization to renamed categories using the name mapping
                    for article, assigned_category in zip(batch, batch_assignments):
                        if assigned_category and assigned_category in existing_categories:
                            # Map old category name to new name
                            new_category_name = name_mapping.get(assigned_category, assigned_category)
                            if new_category_name in renamed_categories:
                                renamed_categories[new_category_name].append(article)
                        # If None or "NONE", discard the article (orphaned)
                    
                    # Use renamed categories
                    relevant_categories = renamed_categories
                else:
                    # Regular batch: just recategorize
                    batch_assignments = self._recategorize_batch(batch, existing_categories)
                    
                    for article, assigned_category in zip(batch, batch_assignments):
                        if assigned_category and assigned_category in existing_categories:
                            relevant_categories[assigned_category].append(article)
                        # If None or "NONE", discard the article (orphaned)
        elif relevant_categories:
            # Even if no recategorization, still rename categories
            print(f"\n🏷️  Renaming categories to better match their articles...")
            relevant_categories = self._rename_categories_batch(relevant_categories)
        
        return relevant_categories
    
    def _check_batch_category_relevance(self, category_articles_pairs: List[tuple]) -> List[bool]:
        """
        Check relevance of multiple categories in a single API call.
        
        Args:
            category_articles_pairs: List of (category_name, articles_list) tuples
        
        Returns:
            List of booleans, True if category is relevant
        """
        # Create summary of all categories and their articles
        categories_text = "\n\n".join([
            f"Category: {category}\nArticles ({len(articles)}):\n" + "\n".join([
                f"  - {article.get('title', 'No title')[:100]}"
                for article in articles[:5]  # Show first 5 articles
            ])
            for category, articles in category_articles_pairs
        ])
        
        prompt = f"""You are analyzing whether articles are actually on-topic for their assigned categories.

Categories and their articles:
{categories_text}

For each category above, determine if the articles are actually relevant and on-topic for that category.

Return "true" if at least 2 articles are clearly relevant to the category.
Return "false" if the articles are not relevant, too niche, or the category doesn't make sense for these articles.

Return a JSON array of booleans, one for each category in order (true = relevant, false = not relevant).
Example format: [true, false, true, true, false]

Return ONLY the JSON array, nothing else."""
        
        try:
            response = self._call_openrouter([
                {"role": "system", "content": "You are a helpful assistant that analyzes article-category relevance. Always respond with only a valid JSON array of booleans."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            results = json.loads(response)
            
            # Ensure we have the right number of results
            if isinstance(results, list) and len(results) == len(category_articles_pairs):
                return results
            else:
                print(f"   Warning: Unexpected batch validation result format, keeping all categories")
                return [True] * len(category_articles_pairs)
        except Exception as e:
            print(f"   Warning: Error checking batch category relevance: {e}")
            # On error, assume relevant (safer to keep than remove)
            return [True] * len(category_articles_pairs)
    
    def _rename_categories_batch(self, categorized_articles: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """
        Rename categories to better fit their articles in a single batched API call.
        
        Args:
            categorized_articles: Dictionary mapping category names to article lists
        
        Returns:
            Dictionary with renamed categories
        """
        # Create summary of all categories and their articles
        categories_text = "\n\n".join([
            f"Current Category Name: {category}\nArticles ({len(articles)}):\n" + "\n".join([
                f"  - {article.get('title', 'No title')[:150]}"
                for article in articles[:10]  # Show up to 10 articles
            ])
            for category, articles in categorized_articles.items()
        ])
        
        prompt = f"""You are renaming categories to better match the articles they contain.

Categories and their articles:
{categories_text}

For each category above, suggest a better, more specific category name that accurately describes the articles in that category. The new name should:
- Be specific and descriptive
- Accurately reflect the common theme of the articles
- Be concise (preferably 2-5 words)
- Include relevant names, organizations, or policies if appropriate

Return a JSON object mapping old category names to new category names.
Example format: {{"Old Category 1": "New Category 1", "Old Category 2": "New Category 2", ...}}

If a category name is already good and doesn't need changing, keep it the same in the mapping.

Return ONLY the JSON object, nothing else."""
        
        try:
            response = self._call_openrouter([
                {"role": "system", "content": "You are a helpful assistant that renames categories to better match their content. Always respond with only a valid JSON object."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            rename_mapping = json.loads(response)
            
            # Create new dictionary with renamed categories
            renamed_categories = {}
            for old_name, articles in categorized_articles.items():
                new_name = rename_mapping.get(old_name, old_name)  # Use old name if not in mapping
                renamed_categories[new_name] = articles
                if new_name != old_name:
                    print(f"   Renamed '{old_name}' → '{new_name}'")
            
            return renamed_categories
        except Exception as e:
            print(f"   Warning: Error renaming categories: {e}")
            # On error, return original categories
            return categorized_articles
    
    def _recategorize_batch(self, articles: List[Dict], categories: List[str]) -> List[Optional[str]]:
        """
        Recategorize a batch of articles into existing categories.
        
        Args:
            articles: List of article dictionaries to recategorize
            categories: List of existing category names
        
        Returns:
            List of assigned category names (or None if no good fit)
        """
        # Create article summaries
        articles_text = "\n\n".join([
            f"Article {i+1}:\nTitle: {article.get('title', 'No title')}\nDescription: {article.get('description', 'No description')[:300]}"
            for i, article in enumerate(articles)
        ])
        
        prompt = f"""You are categorizing news articles. For each article below, assign it to ONE of these existing categories:

Categories: {', '.join(categories)}

Articles:
{articles_text}

For each article, if it fits well into one of these categories, return the category name exactly as shown.
If an article does NOT fit well into any category, return "NONE".

Return a JSON array with one category name (or "NONE") for each article in order.
Example format: ["Category Name", "NONE", "Category Name", ...]

Return ONLY the JSON array, nothing else."""
        
        try:
            response = self._call_openrouter([
                {"role": "system", "content": "You are a helpful assistant that categorizes news articles. Always respond with only a valid JSON array."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            assignments = json.loads(response)
            
            # Ensure we have the right number of results
            if isinstance(assignments, list) and len(assignments) == len(articles):
                # Convert "NONE" strings to None
                return [None if (isinstance(a, str) and a.upper() == "NONE") else a for a in assignments]
            else:
                print(f"   Warning: Unexpected recategorization result format")
                return [None] * len(articles)
        except Exception as e:
            print(f"   Warning: Error recategorizing batch: {e}")
            return [None] * len(articles)
    
    def _recategorize_and_rename_combined(self, articles: List[Dict], categories: List[str], 
                                          categorized_articles: Dict[str, List[Dict]]) -> tuple:
        """
        Recategorize articles AND rename all categories in a single API call.
        
        Args:
            articles: List of article dictionaries to recategorize
            categories: List of existing category names
            categorized_articles: Dictionary mapping category names to article lists (current state)
        
        Returns:
            Tuple of (list of assigned category names, renamed categories dictionary, old-to-new name mapping)
        """
        # Create article summaries for recategorization
        articles_text = "\n\n".join([
            f"Article {i+1}:\nTitle: {article.get('title', 'No title')}\nDescription: {article.get('description', 'No description')[:300]}"
            for i, article in enumerate(articles)
        ])
        
        # Create summary of all categories and their articles for renaming
        categories_text = "\n\n".join([
            f"Current Category Name: {category}\nArticles ({len(articles)}):\n" + "\n".join([
                f"  - {article.get('title', 'No title')[:150]}"
                for article in articles[:10]  # Show up to 10 articles
            ])
            for category, articles in categorized_articles.items()
        ])
        
        prompt = f"""You are performing two tasks:

TASK 1: Recategorize articles
For each article below, assign it to ONE of these existing categories: {', '.join(categories)}
If an article does NOT fit well into any category, return "NONE".

TASK 2: Rename categories
For each category below, suggest a better, more specific category name that accurately describes the articles in that category. The new name should be specific, descriptive, concise (2-5 words), and include relevant names/organizations/policies if appropriate.

Articles to recategorize:
{articles_text}

Current categories and their articles:
{categories_text}

Return a JSON object with two keys:
1. "recategorizations": An array with one category name (or "NONE") for each article in order
   Example: ["Category Name", "NONE", "Category Name", ...]
2. "renames": An object mapping old category names to new category names
   Example: {{"Old Category 1": "New Category 1", "Old Category 2": "New Category 2", ...}}
   If a category name is already good, keep it the same in the mapping.

Example format:
{{
  "recategorizations": ["Category Name", "NONE", "Category Name"],
  "renames": {{"Old Category 1": "New Category 1", "Old Category 2": "Old Category 2"}}
}}

Return ONLY the JSON object, nothing else."""
        
        try:
            response = self._call_openrouter([
                {"role": "system", "content": "You are a helpful assistant that recategorizes articles and renames categories. Always respond with only a valid JSON object."},
                {"role": "user", "content": prompt}
            ], temperature=0.3)
            
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            result = json.loads(response)
            
            # Extract recategorizations
            assignments = result.get("recategorizations", [])
            if isinstance(assignments, list) and len(assignments) == len(articles):
                assignments = [None if (isinstance(a, str) and a.upper() == "NONE") else a for a in assignments]
            else:
                print(f"   Warning: Unexpected recategorization result format")
                assignments = [None] * len(articles)
            
            # Extract and apply renames
            rename_mapping = result.get("renames", {})
            renamed_categories = {}
            name_mapping = {}  # Map old names to new names
            for old_name, articles_list in categorized_articles.items():
                new_name = rename_mapping.get(old_name, old_name)  # Use old name if not in mapping
                renamed_categories[new_name] = articles_list.copy()  # Copy to avoid modifying original
                name_mapping[old_name] = new_name
                if new_name != old_name:
                    print(f"   Renamed '{old_name}' → '{new_name}'")
            
            return assignments, renamed_categories, name_mapping
        except Exception as e:
            print(f"   Warning: Error in combined recategorize and rename: {e}")
            # Fallback: just recategorize, keep original category names
            assignments = self._recategorize_batch(articles, categories)
            name_mapping = {cat: cat for cat in categories}  # Identity mapping
            return assignments, categorized_articles, name_mapping

