"""
Video Generator: Creates video from debate script using Eleven Labs (audio) and Runway (video)
"""
import os
import re
import json
import requests
import asyncio
import subprocess
from datetime import datetime
from typing import List, Tuple, Optional
from dotenv import load_dotenv
from search import generate_args
from script_generator import generate_script_from_debate_json, save_script_to_file

load_dotenv()

# API Keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Voice IDs - Using male voices by default
# Carnegie (liberal) - Male voice
# Mellon (conservative) - Male voice (deep male voice)
CARNEGIE_VOICE_ID = os.getenv("ELEVENLABS_CARNEGIE_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam - male voice
MELLON_VOICE_ID = os.getenv("ELEVENLABS_MELLON_VOICE_ID", "VR6AewLTigWG4xSOukaG")  # Arnold - deep male voice


def get_available_voices():
    """
    Get list of available voices from Eleven Labs.
    
    Returns:
        List of voice dictionaries with id, name, etc.
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set in environment")
    
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data.get("voices", [])
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise ValueError("Invalid ELEVENLABS_API_KEY. Please check your API key in the .env file.")
        raise


def list_voices():
    """
    Print available voices from Eleven Labs.
    """
    try:
        voices = get_available_voices()
        print("\n" + "=" * 80)
        print("Available Eleven Labs Voices:")
        print("=" * 80)
        for i, voice in enumerate(voices, 1):
            voice_id = voice.get("voice_id", "N/A")
            name = voice.get("name", "Unknown")
            description = voice.get("description", "")
            print(f"{i}. {name}")
            print(f"   ID: {voice_id}")
            if description:
                print(f"   Description: {description[:100]}...")
            print()
        print("=" * 80)
        print("\nTo use a voice, set it in your .env file:")
        print("ELEVENLABS_CARNEGIE_VOICE_ID=voice_id_here")
        print("ELEVENLABS_MELLON_VOICE_ID=voice_id_here")
        print()
        return voices
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return []


def parse_script(script_text: str) -> List[Tuple[str, str]]:
    """
    Parse script text into list of (speaker, text) tuples.
    Handles formats: **Carnegie:**, **Carnegie**:, CARNEGIE:
    
    Args:
        script_text: The script text with speaker labels
        
    Returns:
        List of (speaker, text) tuples
    """
    segments = []
    lines = script_text.split('\n')
    current_speaker = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for speaker labels - handles multiple formats:
        # **Carnegie:** or **Carnegie**: or **Carnegie**:
        # Match with flexible pattern for colon placement
        carnegie_match = re.match(r'^\*\*Carnegie:?\*\*:?\s*(.*)$', line, re.IGNORECASE)
        mellon_match = re.match(r'^\*\*Mellon:?\*\*:?\s*(.*)$', line, re.IGNORECASE)
        
        if carnegie_match:
            if current_speaker and current_text:
                segments.append((current_speaker, ' '.join(current_text)))
            current_speaker = 'CARNEGIE'
            text = carnegie_match.group(1).strip()
            current_text = [text] if text else []
        elif mellon_match:
            if current_speaker and current_text:
                segments.append((current_speaker, ' '.join(current_text)))
            current_speaker = 'MELLON'
            text = mellon_match.group(1).strip()
            current_text = [text] if text else []
        elif current_speaker:
            # Remove markdown formatting and add to current text
            clean_line = re.sub(r'\*\*', '', line)
            if clean_line:
                current_text.append(clean_line)
    
    # Add the last entry
    if current_speaker and current_text:
        segments.append((current_speaker, ' '.join(current_text)))
    
    return segments


def generate_elevenlabs_audio(text: str, voice_id: str, output_path: str) -> str:
    """
    Generate audio using Eleven Labs API.
    
    Args:
        text: Text to convert to speech
        voice_id: Eleven Labs voice ID
        output_path: Path to save audio file
        
    Returns:
        Path to generated audio file
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set in environment")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    response = requests.post(url, json=data, headers=headers, timeout=60)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    return output_path


async def generate_runway_video(prompt: str, output_path: str) -> str:
    """
    Generate video using Runway API.
    
    Args:
        prompt: Text prompt for video generation
        output_path: Path to save video file
        
    Returns:
        Path to generated video file
    """
    if not RUNWAY_API_KEY:
        raise ValueError("RUNWAY_API_KEY not set in environment")
    
    headers = {
        "Authorization": f"Bearer {RUNWAY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://api.runwayml.com/v1"
    
    # Try multiple possible payload formats
    payloads_to_try = [
        {
            "task_type": "text-to-video",
            "prompt": prompt,
            "duration": 5,
            "ratio": "16:9"
        },
        {
            "type": "text-to-video",
            "prompt": prompt,
            "duration": 5,
            "aspect_ratio": "16:9"
        },
        {
            "prompt": prompt,
            "duration": 5,
            "ratio": "16:9"
        }
    ]
    
    create_url = f"{base_url}/tasks"
    last_error = None
    
    for idx, payload in enumerate(payloads_to_try):
        try:
            create_response = requests.post(create_url, json=payload, headers=headers, timeout=60)
            
            if create_response.status_code in [200, 201]:
                response_data = create_response.json()
                print(f"✓ Runway API success with payload format {idx + 1}")
                break
            else:
                error_text = create_response.text
                try:
                    error_json = create_response.json()
                    error_detail = error_json.get("error", {}).get("message", error_text) if isinstance(error_json.get("error"), dict) else error_json.get("error", error_text)
                except:
                    error_detail = error_text
                last_error = f"Status {create_response.status_code}: {error_detail}"
                print(f"✗ Runway API attempt {idx + 1} failed: {last_error}")
                continue
        except Exception as e:
            last_error = f"Exception: {str(e)}"
            print(f"✗ Runway API attempt {idx + 1} exception: {last_error}")
            continue
    else:
        raise Exception(f"Runway API error (tried {len(payloads_to_try)} formats): {last_error}")
    
    # Get task ID from response
    task_id = response_data.get("id") or response_data.get("task_id")
    if not task_id:
        raise Exception(f"Runway API did not return a task ID. Response: {response_data}")
    
    # Poll for completion
    status_url = f"{base_url}/tasks/{task_id}"
    max_attempts = 60  # 5 minutes max
    print(f"Waiting for Runway video generation (task ID: {task_id})...")
    
    for attempt in range(max_attempts):
        status_response = requests.get(status_url, headers=headers, timeout=30)
        status_response.raise_for_status()
        status_data = status_response.json()
        
        status = status_data.get("status") or status_data.get("state")
        
        if status == "completed" or status == "succeeded":
            # Try different possible response structures
            output = status_data.get("output") or status_data.get("result")
            if isinstance(output, list) and len(output) > 0:
                video_url = output[0].get("url") or output[0].get("video_url")
            elif isinstance(output, dict):
                video_url = output.get("url") or output.get("video_url")
            else:
                video_url = status_data.get("video_url") or status_data.get("url")
            
            if video_url:
                # Download the video
                print(f"Downloading video from {video_url}...")
                video_response = requests.get(video_url, timeout=120)
                video_response.raise_for_status()
                with open(output_path, 'wb') as f:
                    f.write(video_response.content)
                print(f"✓ Video downloaded to {output_path}")
                return output_path
            else:
                raise Exception(f"Runway completed but no video URL found. Response: {status_data}")
        elif status == "failed" or status == "error":
            error_msg = status_data.get("error") or status_data.get("message", "Unknown error")
            raise Exception(f"Runway video generation failed: {error_msg}")
        
        # Log progress every 6 attempts (30 seconds)
        if attempt % 6 == 0:
            print(f"  Still processing... (attempt {attempt + 1}/{max_attempts})")
        
        await asyncio.sleep(5)  # Wait 5 seconds before next poll
    
    raise Exception("Runway video generation timed out after 5 minutes")


def combine_audio_video(audio_path: str, video_path: str, output_path: str):
    """
    Combine audio and video using ffmpeg.
    
    Args:
        audio_path: Path to audio file
        video_path: Path to video file
        output_path: Path to save combined video
    """
    subprocess.run([
        'ffmpeg', '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        output_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def concatenate_videos(video_paths: List[str], output_path: str):
    """
    Concatenate multiple video files using ffmpeg.
    
    Args:
        video_paths: List of video file paths
        output_path: Path to save concatenated video
    """
    # Create concat file for ffmpeg
    concat_file = "concat_list.txt"
    with open(concat_file, 'w') as f:
        for video_path in video_paths:
            f.write(f"file '{os.path.abspath(video_path)}'\n")
    
    try:
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        if os.path.exists(concat_file):
            os.remove(concat_file)


async def generate_audio_from_script(script_path: str = "new_script.txt", output_dir: str = "audio_output"):
    """
    Main function to generate audio from script (voices only, no video).
    
    Args:
        script_path: Path to script file
        output_dir: Directory to save audio files
    """
    print("=" * 80)
    print("🎤 Audio Generator - Creating audio from debate script")
    print("=" * 80)
    
    # Check API key
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set in environment")
    
    # Using male voices by default
    print(f"\n🎤 Using male voices:")
    print(f"   Carnegie (liberal): Voice ID {CARNEGIE_VOICE_ID}")
    print(f"   Mellon (conservative): Voice ID {MELLON_VOICE_ID}")
    print()
    
    # Read script
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script file not found: {script_path}")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        script_text = f.read()
    
    print(f"\n📖 Reading script from {script_path}")
    
    # Parse script
    segments = parse_script(script_text)
    print(f"✓ Parsed {len(segments)} segments")
    
    if not segments:
        raise ValueError("No segments found in script. Ensure it has Carnegie and Mellon labels.")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n🎤 Generating audio files with Eleven Labs...")
    
    # Generate audio for each segment
    audio_files = []
    for i, (speaker, text) in enumerate(segments):
        voice_id = CARNEGIE_VOICE_ID if speaker == "CARNEGIE" else MELLON_VOICE_ID
        audio_filename = f"{i+1:02d}_{speaker}_{text[:30].replace(' ', '_')}.mp3"
        audio_path = os.path.join(output_dir, audio_filename)
        
        print(f"  [{i+1}/{len(segments)}] Generating audio for {speaker}...")
        generate_elevenlabs_audio(text, voice_id, audio_path)
        audio_files.append((speaker, text, audio_path))
        print(f"    ✓ Audio saved to {audio_path}")
    
    print("\n" + "=" * 80)
    print(f"✅ Audio generation complete! {len(audio_files)} audio files saved to {output_dir}/")
    print("=" * 80)
    
    return audio_files


if __name__ == "__main__":
    import sys
    
    # Check for --list-voices flag
    if "--list-voices" in sys.argv or "-l" in sys.argv:
        list_voices()
        sys.exit(0)
    
    script_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "new_script.txt"
    output_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "audio_output"
    
    asyncio.run(generate_audio_from_script(script_path, output_dir))

