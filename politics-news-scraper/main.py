"""
Main script for politics news scraper and categorizer.
Fetches recent politics articles, dynamically categorizes them, and outputs results.
"""
import json
from datetime import datetime
from news_scraper import NewsScraper
from categorizer import DynamicCategorizer
from config import ARTICLES_PER_CATEGORY


def format_output(categorized_articles: dict, output_format: str = "console"):
    """
    Format and output categorized articles.
    
    Args:
        categorized_articles: Dictionary mapping categories to article lists
        output_format: Output format ('console', 'json', or 'both')
    """
    if output_format in ["console", "both"]:
        print("\n" + "="*80)
        print("POLITICS NEWS - CATEGORIZED ARTICLES")
        print("="*80)
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for category, articles in categorized_articles.items():
            if articles:  # Only show categories with articles
                print(f"\n{'─'*80}")
                print(f"📁 CATEGORY: {category.upper()}")
                print(f"{'─'*80}")
                print(f"Articles: {len(articles)}\n")
                
                for i, article in enumerate(articles, 1):
                    title = article.get("title", "No title")
                    source = article.get("source", {}).get("name", "Unknown source")
                    published = article.get("publishedAt", "Unknown date")
                    url = article.get("url", "")
                    description = article.get("description", "")
                    
                    print(f"  {i}. {title}")
                    print(f"     Source: {source} | Published: {published}")
                    if description:
                        print(f"     {description[:150]}...")
                    if url:
                        print(f"     URL: {url}")
                    print()
        
        print("="*80)
        print(f"Total categories: {len([cat for cat, arts in categorized_articles.items() if arts])}")
        print(f"Total articles: {sum(len(arts) for arts in categorized_articles.values())}")
        print("="*80)
    
    if output_format in ["json", "both"]:
        output_data = {
            "generated_at": datetime.now().isoformat(),
            "categories": {
                category: [
                    {
                        "title": article.get("title"),
                        "source": article.get("source", {}).get("name"),
                        "publishedAt": article.get("publishedAt"),
                        "url": article.get("url"),
                        "description": article.get("description"),
                    }
                    for article in articles
                ]
                for category, articles in categorized_articles.items()
                if articles
            }
        }
        
        filename = f"categorized_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ JSON output saved to: {filename}")


def main():
    """Main execution function."""
    print("🚀 Starting Politics News Scraper and Categorizer...")
    print("-" * 80)
    
    try:
        # Step 1: Fetch articles
        print("📰 Fetching recent politics articles...")
        scraper = NewsScraper()
        articles = scraper.fetch_recent_politics_articles(days_back=7, max_articles=50)
        
        if not articles:
            print("❌ No articles found. Please check your News API key and connection.")
            return
        
        print(f"✅ Fetched {len(articles)} articles")
        
        # Step 2: Generate categories
        print("\n🧠 Generating dynamic categories...")
        categorizer = DynamicCategorizer()
        
        # Create summaries for category generation
        article_summaries = [
            scraper.format_article_for_categorization(article)
            for article in articles[:20]  # Use first 20 for category generation
        ]
        
        categories = categorizer.generate_categories(article_summaries)
        print(f"✅ Generated {len(categories)} categories: {', '.join(categories)}")
        
        # Step 3: Categorize articles
        print("\n📂 Categorizing articles...")
        categorized_articles = categorizer.categorize_articles(articles, categories)
        print("✅ Categorization complete")
        
        # Step 4: Output results
        print("\n📊 Generating output...")
        format_output(categorized_articles, output_format="both")
        
        print("\n✨ Process completed successfully!")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nPlease ensure you have set up your .env file with:")
        print("  - NEWS_API_KEY=your_news_api_key")
        print("  - OPENROUTER_API_KEY=your_openrouter_api_key")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

