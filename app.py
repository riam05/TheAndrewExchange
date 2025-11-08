"""
Political Debate Analyzer API
FastAPI backend for analyzing political debates and generating trending topics.
"""
import os
import json
import requests
import asyncio
import glob
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from search import generate_args
from politics_news_scraper.news_scraper import NewsScraper
from politics_news_scraper.categorizer import DynamicCategorizer
from script_generator import generate_script_from_debate_json, save_script_to_file
from videogenerator import generate_audio_from_script

app = FastAPI(title="Political Debate Analyzer API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve audio files
if os.path.exists("audio_output"):
    app.mount("/audio", StaticFiles(directory="audio_output"), name="audio")

class TopicRequest(BaseModel):
    topic: str

@app.post('/api/analyze')
async def analyze_topic(request: TopicRequest):
    """
    Analyze a political topic from liberal and conservative perspectives.
    Generates debate JSON → script → audio files.
    
    Args:
        request: TopicRequest containing the topic to analyze
        
    Returns:
        dict: Analysis results with audio files
    """
    topic = request.topic.strip()
    
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    
    try:
        print(f"\n{'='*80}")
        print(f"🎯 FULL PIPELINE: Analyzing '{topic}'")
        print(f"{'='*80}")
        
        # Step 1: Generate debate JSON using OpenRouter API
        print("📊 Step 1/4: Generating debate arguments...")
        headers, payload = generate_args(topic)
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Save debate JSON to file
        os.makedirs("results", exist_ok=True)
        safe_filename = "".join(c if c.isalnum() else "_" for c in topic.lower())[:100]
        output_path = os.path.join("results", f"{safe_filename}.json")
        
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"   ✓ Debate JSON saved to {output_path}")
        
        # Step 2: Extract and parse debate JSON from the response
        print("📝 Step 2/4: Parsing debate content...")
        try:
            content = result["choices"][0]["message"]["content"]
            
            # Remove markdown code blocks if present
            if content.strip().startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            debate_json = json.loads(content)
            print(f"   ✓ Debate JSON parsed successfully")
            
            # Step 3: Generate script from debate JSON
            print("🎬 Step 3/4: Generating debate script...")
            script = generate_script_from_debate_json(debate_json)
            script_path = save_script_to_file(script, "new_script.txt")
            print(f"   ✓ Script saved to {script_path}")
            
            # Step 4: Generate audio files from the script
            print("🎤 Step 4/4: Generating audio files...")
            
            # Clear old audio files first
            audio_dir = "audio_output"
            if os.path.exists(audio_dir):
                print(f"   🗑️  Clearing old audio files...")
                shutil.rmtree(audio_dir)
            os.makedirs(audio_dir, exist_ok=True)
            
            # Generate audio files
            try:
                audio_files = await generate_audio_from_script(script_path, audio_dir)
                print(f"   ✓ Generated {len(audio_files)} audio files")
                
                # Get audio file info for response
                audio_file_list = []
                for speaker, text, audio_path in audio_files:
                    filename = os.path.basename(audio_path)
                    audio_file_list.append({
                        "filename": filename,
                        "path": f"/audio/{filename}",
                        "speaker": speaker
                    })
                
                print(f"\n{'='*80}")
                print(f"✅ PIPELINE COMPLETE!")
                print(f"   - Debate JSON: {output_path}")
                print(f"   - Script: {script_path}")
                print(f"   - Audio files: {len(audio_file_list)} segments in {audio_dir}/")
                print(f"{'='*80}\n")
                
                return {
                    "success": True,
                    "script": script,
                    "script_path": script_path,
                    "debate_data": debate_json,
                    "saved_to": output_path,
                    "audio_files": audio_file_list,
                    "audio_count": len(audio_file_list)
                }
                
            except Exception as audio_error:
                print(f"   ✗ Audio generation failed: {audio_error}")
                # Return script without audio if audio generation fails
                return {
                    "success": True,
                    "script": script,
                    "script_path": script_path,
                    "debate_data": debate_json,
                    "saved_to": output_path,
                    "error": f"Audio generation failed: {str(audio_error)}",
                    "audio_files": []
                }
            
        except (json.JSONDecodeError, KeyError, Exception) as e:
            print(f"   ✗ Script generation error: {e}")
            # If script generation fails, still return the original data
            return {
                "success": True,
                "data": result,
                "saved_to": output_path,
                "error": f"Script generation failed: {str(e)}",
                "audio_files": []
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

@app.get('/api/audio-files')
async def get_audio_files():
    """Get list of audio files from audio_output directory"""
    import glob
    
    audio_dir = "audio_output"
    if not os.path.exists(audio_dir):
        return {"audio_files": []}
    
    # Get all MP3 files sorted by filename
    audio_files = sorted(glob.glob(os.path.join(audio_dir, "*.mp3")))
    
    # Parse file info
    audio_list = []
    for file_path in audio_files:
        filename = os.path.basename(file_path)
        # Extract speaker from filename (format: 01_CARNEGIE_... or 01_MELLON_...)
        if "CARNEGIE" in filename:
            speaker = "CARNEGIE"
        elif "MELLON" in filename:
            speaker = "MELLON"
        else:
            speaker = "UNKNOWN"
        
        audio_list.append({
            "filename": filename,
            "path": f"/audio/{filename}",
            "speaker": speaker
        })
    
    return {"audio_files": audio_list}

