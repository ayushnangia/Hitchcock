from agents.story_boarder.db_client import StoryboardDBClient

class AudioStorage:
    """Storage class for audio-related data"""
    
    def __init__(self):
        """Initialize the storage with database client"""
        self.db = StoryboardDBClient()
    
    def get_script_by_id(self, scene_id: str):
        """Get script data for a specific scene"""
        return self.db.get_script_by_id(scene_id)
    
    def load_shot_image_specs(self):
        """Load all shot image specifications"""
        return self.db.load_shot_image_specs() 