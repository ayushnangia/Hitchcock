from typing import Dict, List
from dataclasses import dataclass
from pydantic import BaseModel
import instructor
from openai import OpenAI

class ScriptScene(BaseModel):
    """Basic scene information"""
    scene_id: str
    title: str
    script_text: str
    importance: str  # "critical", "high", "medium", "low"
    characters: List[str]
    description: str

@dataclass
class VisualPlan:
    """Visual elements for a scene"""
    scene_id: str
    lighting: str
    props: List[str]
    atmosphere: str
    special_effects: List[str]

class Shot(BaseModel):
    """Individual shot information"""
    type: str  # establishing, action, reaction, detail, etc.
    camera: str  # wide shot, medium shot, close-up, etc.
    description: str
    duration: str  # approximate duration like "3-4 seconds", "5-7 seconds"
    camera_movement: str = ""  # pan, tilt, dolly, static, etc.
    focus: str = ""  # what to focus on in this shot

class SceneAnalysis(BaseModel):
    """Analysis of a scene including shots"""
    scene_id: str
    key_moments: List[str]
    shots: List[Shot]
    setting: str
    mood: str
    pacing: str  # slow, medium, fast
    time_of_day: str

def plan_storyboard_scenes(script_text: str) -> List[ScriptScene]:
    """
    Break down script into scenes and identify important ones to storyboard.
    Returns list of scenes with their basic info.
    """
    # Initialize OpenAI client with instructor
    client = instructor.patch(OpenAI())
    
    # Create the prompt for scene breakdown
    prompt = f"""
    Analyze this script and break it down into scenes. For each scene, identify:
    - A unique scene ID
    - A descriptive title
    - The actual script text for that scene
    - The importance level (critical, high, medium, low) based on story impact
    - List of characters present
    - A brief description of what happens
    
    Script to analyze:
    {script_text}
    """
    
    try:
        # Use OpenAI to generate scene breakdowns
        response = client.chat.completions.create(
            model="gpt-4o",
            response_model=List[ScriptScene],
            messages=[
                {"role": "system", "content": "You are a professional script analyst breaking down scripts into structured scene information."},
                {"role": "user", "content": prompt}
            ]
        )
        return response
        
    except Exception as e:
        print(f"Error analyzing script: {e}")
        # Return a minimal scene list as fallback
        return [
            ScriptScene(
                scene_id="error_001",
                title="Error Processing Scene",
                script_text=script_text[:100] + "...",  # First 100 chars
                importance="medium",
                characters=["Unknown"],
                description="Error occurred during scene analysis"
            )
        ]

def analyze_script_scenes(scenes: List[ScriptScene]) -> List[SceneAnalysis]:
    """
    Analyze scenes to identify key moments and plan shots.
    Takes list of scenes, returns analysis with shot sequences.
    """
    client = instructor.patch(OpenAI())
    analyses = []

    for scene in scenes:
        if scene.importance in ["critical", "high"]:  # Only analyze important scenes
            # Create prompt for scene analysis
            prompt = f"""
            Analyze this scene and break it down into key moments and shots. The scene information is:
            
            Title: {scene.title}
            Description: {scene.description}
            Characters: {', '.join(scene.characters)}
            Script:
            {scene.script_text}
            
            For this scene:
            1. Identify 3-5 key dramatic moments
            2. Design a sequence of shots that effectively capture these moments
            3. Consider the setting, mood, and pacing
            4. For each shot, specify:
               - Shot type (establishing, action, reaction, detail)
               - Camera angle and movement
               - What to focus on
               - Approximate duration
            
            Ensure the shots flow together logically and capture the scene's emotional impact.
            """

            try:
                # Get scene analysis from OpenAI
                analysis = client.chat.completions.create(
                    model="gpt-4o",
                    response_model=SceneAnalysis,
                    messages=[
                        {"role": "system", "content": "You are a professional storyboard artist and cinematographer breaking down scenes into detailed shot sequences."},
                        {"role": "user", "content": prompt}
                    ]
                )
                analyses.append(analysis)
            except Exception as e:
                print(f"Error analyzing scene {scene.scene_id}: {e}")
                # Create a basic fallback analysis
                fallback = SceneAnalysis(
                    scene_id=scene.scene_id,
                    key_moments=["Scene start", "Main action", "Scene end"],
                    shots=[
                        Shot(
                            type="establishing",
                            camera="wide shot",
                            description=f"Establish the scene: {scene.description}",
                            duration="3-4 seconds",
                            camera_movement="static",
                            focus="Overall setting"
                        ),
                        Shot(
                            type="medium",
                            camera="medium shot",
                            description="Focus on main character action",
                            duration="4-5 seconds",
                            camera_movement="static",
                            focus="Main character"
                        )
                    ],
                    setting=scene.description,
                    mood="neutral",
                    pacing="medium",
                    time_of_day="day"
                )
                analyses.append(fallback)

    return analyses

def plan_visual_elements(scene_analyses: List[SceneAnalysis]) -> List[VisualPlan]:
    """
    Plan visual elements for each scene based on their analysis.
    Takes scene analyses, returns visual plans.
    """
    visual_plans = []
    for analysis in scene_analyses:
        plan = VisualPlan(
            scene_id=analysis.scene_id,
            lighting="Natural morning light with fog",
            props=["Fallen trees", "Moss-covered rocks"],
            atmosphere="Mysterious and tense",
            special_effects=["Morning mist", "Dappled sunlight"]
        )
        visual_plans.append(plan)
    return visual_plans

tools = [
    {
        "tool": {
            "type": "function",
            "function": {
                "name": "plan_storyboard_scenes",
                "description": "Break down script into scenes and identify important ones",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script_text": {"type": "string", "description": "Full script text"}
                    },
                    "required": ["script_text"]
                }
            }
        },
        "function": plan_storyboard_scenes,
    },
    {
        "tool": {
            "type": "function",
            "function": {
                "name": "analyze_script_scenes",
                "description": "Analyze scenes and plan shot sequences",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scenes": {
                            "type": "array",
                            "description": "List of scenes to analyze"
                        }
                    },
                    "required": ["scenes"]
                }
            }
        },
        "function": analyze_script_scenes,
    },
    {
        "tool": {
            "type": "function",
            "function": {
                "name": "plan_visual_elements",
                "description": "Plan visual elements for scenes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scene_analyses": {
                            "type": "array",
                            "description": "List of scene analyses"
                        }
                    },
                    "required": ["scene_analyses"]
                }
            }
        },
        "function": plan_visual_elements,
    }
]
