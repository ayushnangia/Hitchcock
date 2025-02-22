import json
import os
from typing import List, Optional
from .tools import ScriptScene, SceneAnalysis, VisualPlan, ShotImageSpec

class StoryboardStorage:
    """Handles persistent storage for storyboard pipeline data"""
    
    def __init__(self, storage_dir: str = "data/storyboard"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
    def _get_scene_file_path(self) -> str:
        return os.path.join(self.storage_dir, "scenes.json")
        
    def _get_analysis_file_path(self) -> str:
        return os.path.join(self.storage_dir, "scene_analyses.json")
        
    def _get_visual_plan_file_path(self) -> str:
        return os.path.join(self.storage_dir, "visual_plans.json")

    def _get_shot_specs_file_path(self) -> str:
        return os.path.join(self.storage_dir, "shot_image_specs.json")
    
    def save_scenes(self, scenes: List[ScriptScene]) -> None:
        """Save scene data to file"""
        with open(self._get_scene_file_path(), 'w') as f:
            json.dump([scene.model_dump() for scene in scenes], f, indent=2)
            
    def load_scenes(self) -> List[ScriptScene]:
        """Load scene data from file"""
        try:
            with open(self._get_scene_file_path(), 'r') as f:
                data = json.load(f)
                return [ScriptScene(**scene_data) for scene_data in data]
        except FileNotFoundError:
            return []
            
    def save_scene_analyses(self, analyses: List[SceneAnalysis]) -> None:
        """Save scene analyses to file"""
        with open(self._get_analysis_file_path(), 'w') as f:
            json.dump([analysis.model_dump() for analysis in analyses], f, indent=2)
            
    def load_scene_analyses(self) -> List[SceneAnalysis]:
        """Load scene analyses from file"""
        try:
            with open(self._get_analysis_file_path(), 'r') as f:
                data = json.load(f)
                return [SceneAnalysis(**analysis_data) for analysis_data in data]
        except FileNotFoundError:
            return []
            
    def save_visual_plans(self, plans: List[VisualPlan]) -> None:
        """Save visual plans to file"""
        with open(self._get_visual_plan_file_path(), 'w') as f:
            # Convert VisualPlan dataclass instances to dictionaries
            plan_dicts = []
            for plan in plans:
                plan_dict = {
                    'scene_id': plan.scene_id,
                    'lighting': plan.lighting,
                    'props': plan.props,
                    'atmosphere': plan.atmosphere,
                    'special_effects': plan.special_effects
                }
                plan_dicts.append(plan_dict)
            json.dump(plan_dicts, f, indent=2)
            
    def load_visual_plans(self) -> List[VisualPlan]:
        """Load visual plans from file"""
        try:
            with open(self._get_visual_plan_file_path(), 'r') as f:
                data = json.load(f)
                return [VisualPlan(**plan_data) for plan_data in data]
        except FileNotFoundError:
            return []

    def save_shot_image_specs(self, specs: List[ShotImageSpec]) -> None:
        """Save shot image specifications to file"""
        with open(self._get_shot_specs_file_path(), 'w') as f:
            json.dump([spec.model_dump() for spec in specs], f, indent=2) 