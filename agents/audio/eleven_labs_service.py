import os
import requests
from pathlib import Path
from typing import Optional

class ElevenLabsService:
    """Service for interacting with Eleven Labs API"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVEN_LABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVEN_LABS_API_KEY environment variable not set")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        # Create output directory if it doesn't exist
        self.output_dir = Path("output/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_audio(
        self, 
        text: str, 
        voice_id: str = "JBFqnCBsd6RMkjVDRZzb",  # Default voice - "Rachel"
        model_id: str = "eleven_multilingual_v2",
        scene_id: str = None
    ) -> Optional[str]:
        """
        Generate audio from text using Eleven Labs API
        
        Args:
            text: The text to convert to speech
            voice_id: The ID of the voice to use
            model_id: The ID of the model to use
            
        Returns:
            Path to the generated audio file or None if generation failed
        """
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            
            # Generate a filename based on first few words of text
            filename = scene_id
            output_path = self.output_dir / f"{filename}.mp3"
            
            # Save the audio content
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            return str(output_path)
            
        except requests.exceptions.RequestException as e:
            print(f"Error generating audio: {e}")
            return None 