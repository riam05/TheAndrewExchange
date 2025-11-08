import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
AIRIA_API_KEY = os.getenv("AIRIA_API_KEY")

def generate_args(topic):
    """Generate the arguments for the API call"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""
        Explain the current debate between liberals and conservatives on the topic: "{topic}". Don't be afraid to be opinionated.
        Return **only valid JSON** describing both sides of the issue, with explicit stance labels. Use this schema exactly:
        {{
        "topic": "{topic}",
        "sides": [
            {{
            "id": "A",
            "label": "liberal",
            "arguments": ["arguments for a liberal side", ...],
            "sources": ["url1", "url2", ...]
            }},
            {{
            "id": "B",
            "label": "conservative",
            "arguments": ["arguments for a conservative side", ...],
            "sources": ["url1", "url2", ...]
            }}
        ]
        }}
        Make sure all arguments are concise and supported by citations from RECENT sources.
        """
    
    payload = {
        "model": "perplexity/sonar-pro-search",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    
    return headers, payload

# topic = "The current U.S. government shutdown debate"
# headers, payload = generate_args(topic)

# response = requests.post(
#     "https://openrouter.ai/api/v1/chat/completions",
#     headers=headers,
#     data=json.dumps(payload)
# )

# data = response.json()

# os.makedirs("results", exist_ok=True)
# output_path = os.path.join("results", "government_shutdown.json")

with open(output_path, "w") as f:
    json.dump(data, f, indent=2)
