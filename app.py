"""
Political Debate Analyzer API
FastAPI backend for analyzing political debates and generating trending topics.
"""
import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from search import generate_args
from politics_news_scraper.news_scraper import NewsScraper
from politics_news_scraper.categorizer import DynamicCategorizer
from script_generator import generate_script_from_debate_json, save_script_to_file

app = FastAPI(title="Political Debate Analyzer API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TopicRequest(BaseModel):
    topic: str

@app.post('/api/analyze')
async def analyze_topic(request: TopicRequest):
    """
    Analyze a political topic from liberal and conservative perspectives.
    
    Args:
        request: TopicRequest containing the topic to analyze
        
    Returns:
        dict: Analysis results with both political perspectives
    """
    topic = request.topic.strip()
    
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    
    try:
        # Generate API call arguments
        headers, payload = generate_args(topic)
        
        # Make the API call to OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Save results to file
        os.makedirs("results", exist_ok=True)
        safe_filename = "".join(c if c.isalnum() else "_" for c in topic.lower())[:100]
        output_path = os.path.join("results", f"{safe_filename}.json")
        
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        
        # Extract debate JSON from the response
        try:
            content = result["choices"][0]["message"]["content"]
            # Parse the JSON content
            if content.strip().startswith("```"):
                # Remove markdown code blocks
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            debate_json = json.loads(content)
            
            # Generate script from debate JSON
            script = generate_script_from_debate_json(debate_json)
            
            # Save script to new_script.txt
            script_path = save_script_to_file(script, "new_script.txt")
            
            return {
                "success": True,
                "script": script,
                "script_path": script_path,
                "debate_data": debate_json,
                "saved_to": output_path
            }
        except (json.JSONDecodeError, KeyError, Exception) as e:
            print(f"Error generating script: {e}")
            # If script generation fails, still return the original data
            return {
                "success": True,
                "data": result,
                "saved_to": output_path,
                "error": f"Script generation failed: {str(e)}"
            }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"API request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing topic: {str(e)}")

@app.get('/api/health')
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get('/api/trending-topics')
async def get_trending_topics():
    """Get trending political topics from recent news"""
    
    # Fallback topics if API fails
    fallback_topics = [
        "Government funding",
        "Election updates",
        "Foreign policy",
        "Healthcare reform",
        "Climate policy"
    ]
    
    try:
        # Fetch recent politics articles
        scraper = NewsScraper()
        articles = scraper.fetch_recent_politics_articles(days_back=3, max_articles=20)
        
        if not articles:
            print("No articles found, using fallback topics")
            return {"topics": fallback_topics}
        
        # Generate topics using categorizer
        cat = DynamicCategorizer()
        article_summaries = [
            scraper.format_article_for_categorization(article)
            for article in articles[:10]
        ]
        
        # Get categories as trending topics
        topics = cat.generate_categories(article_summaries, num_categories=5)
        
        return {"topics": topics if topics else fallback_topics}
        
    except Exception as e:
        print(f"Error fetching trending topics: {e}")
        return {"topics": fallback_topics}

