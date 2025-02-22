from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class AudioScript:
    """Data model for script audio information"""
    scene_id: str
    title: str
    script_text: str
    characters: List[str]
    description: str
    
@dataclass
class AudioGeneration:
    """Data model for audio generation settings"""
    script: AudioScript
    voice_settings: Dict[str, str]
    background_music: Optional[str] = None
    sound_effects: Optional[List[str]] = None 