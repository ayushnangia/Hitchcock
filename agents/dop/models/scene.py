from typing import Dict, List
from enum import Enum
from pydantic import Field
from .base import HitchcockBaseModel

class CameraAngle(str, Enum):
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    BIRDS_EYE = "birds_eye"
    LOW_ANGLE = "low_angle"
    DUTCH_ANGLE = "dutch_angle"
    OVER_SHOULDER = "over_shoulder"

class CharacterDescription(HitchcockBaseModel):
    name: str
    age: str
    gender: str
    physical_appearance: Dict[str, str] = Field(
        ...,
        description="Build, height, hair, eyes, skin details"
    )
    clothing: Dict[str, str] = Field(
        ...,
        description="Outfit details with symbolic meaning"
    )
    demeanor: Dict[str, str] = Field(
        ...,
        description="Posture, movements, emotional expressions"
    )

class ScenePanel(HitchcockBaseModel):
    panel_id: str
    description: str
    visuals: Dict[str, str] = Field(
        ...,
        description="Lighting, colors, key visual elements"
    )
    camera_angle: CameraAngle
    character_focus: List[str]

class StoryboardRequest(HitchcockBaseModel):
    characters: Dict[str, CharacterDescription]
    panels: List[ScenePanel]
    visual_theme: Dict[str, str] = Field(
        default={
            "lighting": "soft autumn light",
            "color_palette": "muted tones vs bright hues"
        }
    )
