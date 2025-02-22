import os
from typing import List
from .tools import ScriptScene, SceneAnalysis, VisualPlan, ShotImageSpec
from .db_client import StoryboardDBClient

class StoryboardStorage:
    """Handles persistent storage for storyboard pipeline data"""
    
    def __init__(self, storage_dir: str = "data/storyboard"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.db = StoryboardDBClient(os.path.join(storage_dir, "storyboard.db"))
    
    def save_scenes(self, scenes: List[ScriptScene]) -> None:
        """Save scene data to database"""
        self.db.save_scenes(scenes)
            
    def load_scenes(self) -> List[ScriptScene]:
        """Load scene data from database"""
        return self.db.load_scenes()
            
    def save_scene_analyses(self, analyses: List[SceneAnalysis]) -> None:
        """Save scene analyses to database"""
        self.db.save_scene_analyses(analyses)
            
    def load_scene_analyses(self) -> List[SceneAnalysis]:
        """Load scene analyses from database"""
        return self.db.load_scene_analyses()
            
    def save_visual_plans(self, plans: List[VisualPlan]) -> None:
        """Save visual plans to database"""
        self.db.save_visual_plans(plans)
            
    def load_visual_plans(self) -> List[VisualPlan]:
        """Load visual plans from database"""
        return self.db.load_visual_plans()

    def save_shot_image_specs(self, specs: List[ShotImageSpec]) -> None:
        """Save shot image specifications to database"""
        self.db.save_shot_image_specs(specs)
            
    def load_shot_image_specs(self) -> List[ShotImageSpec]:
        """Load shot image specifications from database"""
        return self.db.load_shot_image_specs() 