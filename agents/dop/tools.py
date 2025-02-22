from typing import Dict, List
from pathlib import Path
from models.scene import ScenePanel, CameraAngle
from agents.story_boarder.storage import StoryboardStorage
from agents.story_boarder.tools import ShotImageSpec
from agents.dop.image_service import generate_test_image

def generate_shot_images(
    lighting: str = None,
    colors: str = None,
    camera_angle: str = None,
    character_focus: List[str] = None
) -> str:
    """
    Generate images for all shot specifications in the storyboard database.
    Optional parameters can override the values from the database.
    
    Args:
        lighting: Optional lighting override for all shots
        colors: Optional colors override for all shots
        camera_angle: Optional camera angle override for all shots
        character_focus: Optional character focus override for all shots
    
    Returns:
        A string message indicating where the images were created.
    """
    # Initialize storage client
    storage = StoryboardStorage()
    
    # Get all shot specs from storage
    shot_specs = storage.load_shot_image_specs()
    
    # Default values
    size = (1024, 1024)
    output_dir = Path.home() / "hitchcock_output"
    
    for shot_spec in shot_specs:
        # Convert camera type to CameraAngle enum
        # Default to WIDE if camera type not recognized
        try:
            # Use override if provided, otherwise use from database
            cam_type = camera_angle or shot_spec.camera_specs["type"]
            camera_angle_enum = CameraAngle(cam_type.lower().replace(" shot", ""))
        except ValueError:
            camera_angle_enum = CameraAngle.WIDE
            
        # Create ScenePanel from shot spec, using overrides where provided
        scene_panel = ScenePanel(
            panel_id=shot_spec.shot_id,
            description=shot_spec.description,
            visuals={
                "lighting": lighting or shot_spec.visual_elements.get("lighting", "natural daylight"),
                "colors": colors or "natural, vibrant",
                "key_elements": "detailed composition, high quality",
                "mood": shot_spec.visual_elements.get("atmosphere", "neutral")
            },
            camera_angle=camera_angle_enum,
            character_focus=character_focus or shot_spec.characters
        )
        
        generate_test_image(scene_panel)
    
    return f"I have created {len(shot_specs)} images in this directory: {output_dir}"

# Add the image generation tool to the list of available tools
tools = [
    {
        "tool": {
            "type": "function",
            "function": {
                "name": "generate_shot_images",
                "description": "Generate images for all shot specifications that were created by the storyboard artist",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lighting": {
                            "type": "string",
                            "description": "Optional lighting override for all shots"
                        },
                        "colors": {
                            "type": "string",
                            "description": "Optional colors override for all shots"
                        },
                        "camera_angle": {
                            "type": "string",
                            "description": "Optional camera angle override for all shots"
                        },
                        "character_focus": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional character focus override for all shots"
                        }
                    },
                    "required": []
                }
            }
        },
        "function": generate_shot_images,
    }
]
