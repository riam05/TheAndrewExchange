"""
Script Generator using debate JSON to create Carnegie (liberal) vs Mellon (conservative) debate script
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")


def generate_script_from_debate_json(debate_json: dict) -> str:
    """
    Generate a debate script from the debate JSON using the specified prompt.
    
    Args:
        debate_json: Dictionary containing topic and sides (liberal/conservative)
        
    Returns:
        Generated script as string
    """
    if not API_KEY:
        raise ValueError("OPENROUTER_API_KEY is required")
    
    # Extract topic and sides from the JSON
    topic = debate_json.get("topic", "political topic")
    sides = debate_json.get("sides", [])
    
    # Find liberal and conservative sides
    liberal_side = None
    conservative_side = None
    
    for side in sides:
        label = side.get("label", "").lower()
        if "liberal" in label:
            liberal_side = side
        elif "conservative" in label:
            conservative_side = side
    
    # Prepare the input data for the prompt
    input_data = {
        "topic": topic,
        "liberal_arguments": liberal_side.get("arguments", []) if liberal_side else [],
        "conservative_arguments": conservative_side.get("arguments", []) if conservative_side else [],
        "sources": []
    }
    
    # Collect sources
    if liberal_side:
        input_data["sources"].extend(liberal_side.get("sources", []))
    if conservative_side:
        input_data["sources"].extend(conservative_side.get("sources", []))
    
    # Create the prompt as specified
    prompt = f"""You are a news content creator who likes to present information on how two sides of the political spectrum view a topic in the world. There are two sides, Carnegie and Mellon where Mellon represents a conservative side and Carnegie represents the liberal side. Create a transcript that mimics a conversation between Carnegie and Mellon debating this topic from the file inputted in the previous step. Make the points snappy and short, easy to digest for general audiences.

Topic: {input_data['topic']}

Liberal (Carnegie) Arguments:
{chr(10).join(f"- {arg}" for arg in input_data['liberal_arguments'])}

Conservative (Mellon) Arguments:
{chr(10).join(f"- {arg}" for arg in input_data['conservative_arguments'])}

Create a natural, engaging conversation transcript between Carnegie and Mellon. Format it clearly with speaker labels. Make it conversational, with back-and-forth exchanges. Keep each point concise and easy to understand."""
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Use GPT-4o (GPT-5 not available yet, using best available)
    payload = {
        "model": "openai/gpt-4o",  # Using GPT-4o, can change to gpt-4-turbo or anthropic/claude-3.5-sonnet
        "messages": [
            {"role": "system", "content": "You are a news content creator who likes to present information on how two sides of the political spectrum view a topic in the world. There are two sides, Carnegie and Mellon where Mellon represents a conservative side and Carnegie represents the liberal side. Create a transcript that mimics a conversation between Carnegie and Mellon debating this topic from the file inputted in the previous step. Make the points snappy and short, easy to digest for general audiences."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    print("🎬 Generating debate script...")
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        
        script = data["choices"][0]["message"]["content"]
        print("Script generated successfully")
        return script
    
    except Exception as e:
        print(f"Error generating script: {e}")
        raise


def save_script_to_file(script: str, filename: str = "new_script.txt") -> str:
    """
    Save the generated script to a file.
    
    Args:
        script: The script content
        filename: Output filename (default: new_script.txt)
        
    Returns:
        Path to saved file
    """
    output_path = filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(script)
    
    print(f"Script saved to {output_path}")
    return output_path
