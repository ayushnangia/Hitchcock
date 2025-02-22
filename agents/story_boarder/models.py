from typing import Dict, List
from pydantic import BaseModel

class ScriptScene(BaseModel):
    """Basic scene information"""
    scene_id: str
    title: str
    script_text: str
    importance: str  # "critical", "high", "medium", "low"
    characters: List[str]
    description: str

class Shot(BaseModel):
    """Individual shot information"""
    type: str  # establishing, action, reaction, detail, etc.
    camera: str  # wide shot, medium shot, close-up, etc.
    description: str
    duration: str  # approximate duration like "3-4 seconds", "5-7 seconds"
    camera_movement: str = ""  # pan, tilt, dolly, static, etc.
    focus: str = ""  # what to focus on in this shot

class VisualPlan(BaseModel):
    """Visual elements for a scene"""
    scene_id: str
    lighting: str
    props: List[str]
    atmosphere: str
    special_effects: List[str]

class SceneAnalysis(BaseModel):
    """Analysis of a scene including shots"""
    scene_id: str
    key_moments: List[str]
    shots: List[Shot]
    setting: str
    mood: str
    pacing: str  # slow, medium, fast
    time_of_day: str

class ShotImageSpec(BaseModel):
    """Specification for generating an image for a shot"""
    scene_id: str
    shot_id: str  # Will be auto-generated as scene_id + shot number
    description: str  # Combined description of the shot and scene
    camera_specs: Dict[str, str] = {
        "type": "",  # wide shot, medium shot, close-up, etc.
        "movement": "",  # pan, tilt, dolly, static, etc.
        "focus": ""  # what/who to focus on
    }
    visual_elements: Dict[str, str] = {
        "lighting": "",  # lighting setup
        "atmosphere": "",  # overall mood/atmosphere
        "time_of_day": ""
    }
    props: List[str]  # key props that must be visible
    special_effects: List[str]  # special effects to include
    characters: List[str]  # characters present in the shot 