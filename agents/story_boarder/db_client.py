import sqlite3
from typing import List, Optional, Dict
from contextlib import contextmanager
import os
from .tools import ScriptScene, SceneAnalysis, VisualPlan, ShotImageSpec, Shot

class StoryboardDBClient:
    """SQLite database client for storyboard pipeline data"""
    
    def __init__(self, db_path: str = "data/storyboard/storyboard.db"):
        """Initialize database client with path to SQLite database file"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database tables if they don't exist"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create scenes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scenes (
                    scene_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    script_text TEXT NOT NULL,
                    importance TEXT NOT NULL,
                    description TEXT NOT NULL
                )
            """)
            
            # Create scene_characters table (many-to-many relationship)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scene_characters (
                    scene_id TEXT,
                    character_name TEXT,
                    PRIMARY KEY (scene_id, character_name),
                    FOREIGN KEY (scene_id) REFERENCES scenes(scene_id)
                )
            """)
            
            # Create scene_analyses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scene_analyses (
                    scene_id TEXT PRIMARY KEY,
                    setting TEXT NOT NULL,
                    mood TEXT NOT NULL,
                    pacing TEXT NOT NULL,
                    time_of_day TEXT NOT NULL,
                    FOREIGN KEY (scene_id) REFERENCES scenes(scene_id)
                )
            """)
            
            # Create key_moments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS key_moments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scene_id TEXT,
                    moment TEXT NOT NULL,
                    FOREIGN KEY (scene_id) REFERENCES scene_analyses(scene_id)
                )
            """)
            
            # Create shots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scene_id TEXT,
                    type TEXT NOT NULL,
                    camera TEXT NOT NULL,
                    description TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    camera_movement TEXT,
                    focus TEXT,
                    FOREIGN KEY (scene_id) REFERENCES scene_analyses(scene_id)
                )
            """)
            
            # Create visual_plans table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visual_plans (
                    scene_id TEXT PRIMARY KEY,
                    lighting TEXT NOT NULL,
                    atmosphere TEXT NOT NULL,
                    FOREIGN KEY (scene_id) REFERENCES scenes(scene_id)
                )
            """)
            
            # Create props table for visual plans
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visual_plan_props (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scene_id TEXT,
                    prop TEXT NOT NULL,
                    FOREIGN KEY (scene_id) REFERENCES visual_plans(scene_id)
                )
            """)
            
            # Create special effects table for visual plans
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visual_plan_effects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scene_id TEXT,
                    effect TEXT NOT NULL,
                    FOREIGN KEY (scene_id) REFERENCES visual_plans(scene_id)
                )
            """)
            
            # Create shot_image_specs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shot_image_specs (
                    scene_id TEXT,
                    shot_id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    camera_type TEXT,
                    camera_movement TEXT,
                    camera_focus TEXT,
                    lighting TEXT,
                    atmosphere TEXT,
                    time_of_day TEXT
                )
            """)
            
            # Create tables for shot image spec lists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shot_spec_props (
                    shot_id TEXT,
                    prop TEXT NOT NULL,
                    FOREIGN KEY (shot_id) REFERENCES shot_image_specs(shot_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shot_spec_effects (
                    shot_id TEXT,
                    effect TEXT NOT NULL,
                    FOREIGN KEY (shot_id) REFERENCES shot_image_specs(shot_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shot_spec_characters (
                    shot_id TEXT,
                    character_name TEXT NOT NULL,
                    FOREIGN KEY (shot_id) REFERENCES shot_image_specs(shot_id)
                )
            """)
            
            conn.commit()

    def save_scenes(self, scenes: List[ScriptScene]) -> None:
        """Save scene data to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for scene in scenes:
                # Insert scene data
                cursor.execute("""
                    INSERT OR REPLACE INTO scenes (scene_id, title, script_text, importance, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (scene.scene_id, scene.title, scene.script_text, scene.importance, scene.description))
                
                # Delete existing character associations
                cursor.execute("DELETE FROM scene_characters WHERE scene_id = ?", (scene.scene_id,))
                
                # Insert character associations
                for character in scene.characters:
                    cursor.execute("""
                        INSERT INTO scene_characters (scene_id, character_name)
                        VALUES (?, ?)
                    """, (scene.scene_id, character))
            
            conn.commit()

    def load_scenes(self) -> List[ScriptScene]:
        """Load scene data from database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scenes")
            scenes = []
            
            for row in cursor.fetchall():
                # Get characters for this scene
                cursor.execute("""
                    SELECT character_name FROM scene_characters 
                    WHERE scene_id = ?
                """, (row['scene_id'],))
                characters = [r['character_name'] for r in cursor.fetchall()]
                
                scene = ScriptScene(
                    scene_id=row['scene_id'],
                    title=row['title'],
                    script_text=row['script_text'],
                    importance=row['importance'],
                    characters=characters,
                    description=row['description']
                )
                scenes.append(scene)
            
            return scenes

    def save_scene_analyses(self, analyses: List[SceneAnalysis]) -> None:
        """Save scene analyses to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for analysis in analyses:
                # Insert analysis data
                cursor.execute("""
                    INSERT OR REPLACE INTO scene_analyses 
                    (scene_id, setting, mood, pacing, time_of_day)
                    VALUES (?, ?, ?, ?, ?)
                """, (analysis.scene_id, analysis.setting, analysis.mood, 
                     analysis.pacing, analysis.time_of_day))
                
                # Delete existing key moments
                cursor.execute("DELETE FROM key_moments WHERE scene_id = ?", 
                             (analysis.scene_id,))
                
                # Insert key moments
                for moment in analysis.key_moments:
                    cursor.execute("""
                        INSERT INTO key_moments (scene_id, moment)
                        VALUES (?, ?)
                    """, (analysis.scene_id, moment))
                
                # Delete existing shots
                cursor.execute("DELETE FROM shots WHERE scene_id = ?", 
                             (analysis.scene_id,))
                
                # Insert shots
                for shot in analysis.shots:
                    cursor.execute("""
                        INSERT INTO shots 
                        (scene_id, type, camera, description, duration, 
                         camera_movement, focus)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (analysis.scene_id, shot.type, shot.camera, 
                         shot.description, shot.duration, shot.camera_movement,
                         shot.focus))
            
            conn.commit()

    def load_scene_analyses(self) -> List[SceneAnalysis]:
        """Load scene analyses from database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scene_analyses")
            analyses = []
            
            for row in cursor.fetchall():
                scene_id = row['scene_id']
                
                # Get key moments
                cursor.execute("""
                    SELECT moment FROM key_moments 
                    WHERE scene_id = ?
                """, (scene_id,))
                key_moments = [r['moment'] for r in cursor.fetchall()]
                
                # Get shots
                cursor.execute("""
                    SELECT * FROM shots 
                    WHERE scene_id = ?
                """, (scene_id,))
                shots = []
                for shot_row in cursor.fetchall():
                    shot = Shot(
                        type=shot_row['type'],
                        camera=shot_row['camera'],
                        description=shot_row['description'],
                        duration=shot_row['duration'],
                        camera_movement=shot_row['camera_movement'],
                        focus=shot_row['focus']
                    )
                    shots.append(shot)
                
                analysis = SceneAnalysis(
                    scene_id=scene_id,
                    key_moments=key_moments,
                    shots=shots,
                    setting=row['setting'],
                    mood=row['mood'],
                    pacing=row['pacing'],
                    time_of_day=row['time_of_day']
                )
                analyses.append(analysis)
            
            return analyses

    def save_visual_plans(self, plans: List[VisualPlan]) -> None:
        """Save visual plans to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for plan in plans:
                # Insert plan data
                cursor.execute("""
                    INSERT OR REPLACE INTO visual_plans 
                    (scene_id, lighting, atmosphere)
                    VALUES (?, ?, ?)
                """, (plan.scene_id, plan.lighting, plan.atmosphere))
                
                # Delete existing props
                cursor.execute("""
                    DELETE FROM visual_plan_props 
                    WHERE scene_id = ?
                """, (plan.scene_id,))
                
                # Insert props
                for prop in plan.props:
                    cursor.execute("""
                        INSERT INTO visual_plan_props (scene_id, prop)
                        VALUES (?, ?)
                    """, (plan.scene_id, prop))
                
                # Delete existing effects
                cursor.execute("""
                    DELETE FROM visual_plan_effects 
                    WHERE scene_id = ?
                """, (plan.scene_id,))
                
                # Insert effects
                for effect in plan.special_effects:
                    cursor.execute("""
                        INSERT INTO visual_plan_effects (scene_id, effect)
                        VALUES (?, ?)
                    """, (plan.scene_id, effect))
            
            conn.commit()

    def load_visual_plans(self) -> List[VisualPlan]:
        """Load visual plans from database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM visual_plans")
            plans = []
            
            for row in cursor.fetchall():
                scene_id = row['scene_id']
                
                # Get props
                cursor.execute("""
                    SELECT prop FROM visual_plan_props 
                    WHERE scene_id = ?
                """, (scene_id,))
                props = [r['prop'] for r in cursor.fetchall()]
                
                # Get effects
                cursor.execute("""
                    SELECT effect FROM visual_plan_effects 
                    WHERE scene_id = ?
                """, (scene_id,))
                effects = [r['effect'] for r in cursor.fetchall()]
                
                plan = VisualPlan(
                    scene_id=scene_id,
                    lighting=row['lighting'],
                    props=props,
                    atmosphere=row['atmosphere'],
                    special_effects=effects
                )
                plans.append(plan)
            
            return plans

    def save_shot_image_specs(self, specs: List[ShotImageSpec]) -> None:
        """Save shot image specifications to database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for spec in specs:
                # Insert spec data
                cursor.execute("""
                    INSERT OR REPLACE INTO shot_image_specs
                    (scene_id, shot_id, description, camera_type, camera_movement,
                     camera_focus, lighting, atmosphere, time_of_day)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (spec.scene_id, spec.shot_id, spec.description,
                     spec.camera_specs.get('type'), 
                     spec.camera_specs.get('movement'),
                     spec.camera_specs.get('focus'),
                     spec.visual_elements.get('lighting'),
                     spec.visual_elements.get('atmosphere'),
                     spec.visual_elements.get('time_of_day')))
                
                # Handle props
                cursor.execute("DELETE FROM shot_spec_props WHERE shot_id = ?", 
                             (spec.shot_id,))
                for prop in spec.props:
                    cursor.execute("""
                        INSERT INTO shot_spec_props (shot_id, prop)
                        VALUES (?, ?)
                    """, (spec.shot_id, prop))
                
                # Handle effects
                cursor.execute("DELETE FROM shot_spec_effects WHERE shot_id = ?", 
                             (spec.shot_id,))
                for effect in spec.special_effects:
                    cursor.execute("""
                        INSERT INTO shot_spec_effects (shot_id, effect)
                        VALUES (?, ?)
                    """, (spec.shot_id, effect))
                
                # Handle characters
                cursor.execute("""
                    DELETE FROM shot_spec_characters 
                    WHERE shot_id = ?
                """, (spec.shot_id,))
                for character in spec.characters:
                    cursor.execute("""
                        INSERT INTO shot_spec_characters 
                        (shot_id, character_name)
                        VALUES (?, ?)
                    """, (spec.shot_id, character))
            
            conn.commit()

    def load_shot_image_specs(self) -> List[ShotImageSpec]:
        """Load shot image specifications from database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shot_image_specs")
            specs = []
            
            for row in cursor.fetchall():
                shot_id = row['shot_id']
                
                # Get props
                cursor.execute("""
                    SELECT prop FROM shot_spec_props 
                    WHERE shot_id = ?
                """, (shot_id,))
                props = [r['prop'] for r in cursor.fetchall()]
                
                # Get effects
                cursor.execute("""
                    SELECT effect FROM shot_spec_effects 
                    WHERE shot_id = ?
                """, (shot_id,))
                effects = [r['effect'] for r in cursor.fetchall()]
                
                # Get characters
                cursor.execute("""
                    SELECT character_name FROM shot_spec_characters 
                    WHERE shot_id = ?
                """, (shot_id,))
                characters = [r['character_name'] for r in cursor.fetchall()]
                
                spec = ShotImageSpec(
                    scene_id=row['scene_id'],
                    shot_id=shot_id,
                    description=row['description'],
                    camera_specs={
                        'type': row['camera_type'],
                        'movement': row['camera_movement'],
                        'focus': row['camera_focus']
                    },
                    visual_elements={
                        'lighting': row['lighting'],
                        'atmosphere': row['atmosphere'],
                        'time_of_day': row['time_of_day']
                    },
                    props=props,
                    special_effects=effects,
                    characters=characters
                )
                specs.append(spec)
            
            return specs 

    def get_all_scene_ids(self) -> List[str]:
        """Get a list of all scene IDs in the database"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT scene_id FROM scenes ORDER BY scene_id")
            return [row['scene_id'] for row in cursor.fetchall()]

    def get_scene_by_id(self, scene_id: str) -> Optional[ScriptScene]:
        """Get a specific scene by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get scene data
            cursor.execute("SELECT * FROM scenes WHERE scene_id = ?", (scene_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # Get characters for this scene
            cursor.execute("""
                SELECT character_name FROM scene_characters 
                WHERE scene_id = ?
            """, (scene_id,))
            characters = [r['character_name'] for r in cursor.fetchall()]
            
            return ScriptScene(
                scene_id=row['scene_id'],
                title=row['title'],
                script_text=row['script_text'],
                importance=row['importance'],
                characters=characters,
                description=row['description']
            )

    def get_script_text_by_scene_id(self, scene_id: str) -> Optional[str]:
        """Get just the script text for a specific scene"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT script_text FROM scenes WHERE scene_id = ?", (scene_id,))
            row = cursor.fetchone()
            return row['script_text'] if row else None

    def get_scene_analysis_by_id(self, scene_id: str) -> Optional[SceneAnalysis]:
        """Get the analysis for a specific scene"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get analysis data
            cursor.execute("SELECT * FROM scene_analyses WHERE scene_id = ?", (scene_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # Get key moments
            cursor.execute("""
                SELECT moment FROM key_moments 
                WHERE scene_id = ?
            """, (scene_id,))
            key_moments = [r['moment'] for r in cursor.fetchall()]
            
            # Get shots
            cursor.execute("""
                SELECT * FROM shots 
                WHERE scene_id = ?
            """, (scene_id,))
            shots = []
            for shot_row in cursor.fetchall():
                shot = Shot(
                    type=shot_row['type'],
                    camera=shot_row['camera'],
                    description=shot_row['description'],
                    duration=shot_row['duration'],
                    camera_movement=shot_row['camera_movement'],
                    focus=shot_row['focus']
                )
                shots.append(shot)
            
            return SceneAnalysis(
                scene_id=scene_id,
                key_moments=key_moments,
                shots=shots,
                setting=row['setting'],
                mood=row['mood'],
                pacing=row['pacing'],
                time_of_day=row['time_of_day']
            )

    def get_visual_plan_by_id(self, scene_id: str) -> Optional[VisualPlan]:
        """Get the visual plan for a specific scene"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get plan data
            cursor.execute("SELECT * FROM visual_plans WHERE scene_id = ?", (scene_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Get props
            cursor.execute("""
                SELECT prop FROM visual_plan_props 
                WHERE scene_id = ?
            """, (scene_id,))
            props = [r['prop'] for r in cursor.fetchall()]
            
            # Get effects
            cursor.execute("""
                SELECT effect FROM visual_plan_effects 
                WHERE scene_id = ?
            """, (scene_id,))
            effects = [r['effect'] for r in cursor.fetchall()]
            
            return VisualPlan(
                scene_id=scene_id,
                lighting=row['lighting'],
                props=props,
                atmosphere=row['atmosphere'],
                special_effects=effects
            )

    def get_shot_specs_by_scene_id(self, scene_id: str) -> List[ShotImageSpec]:
        """Get all shot specifications for a specific scene"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shot_image_specs WHERE scene_id = ?", (scene_id,))
            specs = []
            
            for row in cursor.fetchall():
                shot_id = row['shot_id']
                
                # Get props
                cursor.execute("""
                    SELECT prop FROM shot_spec_props 
                    WHERE shot_id = ?
                """, (shot_id,))
                props = [r['prop'] for r in cursor.fetchall()]
                
                # Get effects
                cursor.execute("""
                    SELECT effect FROM shot_spec_effects 
                    WHERE shot_id = ?
                """, (shot_id,))
                effects = [r['effect'] for r in cursor.fetchall()]
                
                # Get characters
                cursor.execute("""
                    SELECT character_name FROM shot_spec_characters 
                    WHERE shot_id = ?
                """, (shot_id,))
                characters = [r['character_name'] for r in cursor.fetchall()]
                
                spec = ShotImageSpec(
                    scene_id=row['scene_id'],
                    shot_id=shot_id,
                    description=row['description'],
                    camera_specs={
                        'type': row['camera_type'],
                        'movement': row['camera_movement'],
                        'focus': row['camera_focus']
                    },
                    visual_elements={
                        'lighting': row['lighting'],
                        'atmosphere': row['atmosphere'],
                        'time_of_day': row['time_of_day']
                    },
                    props=props,
                    special_effects=effects,
                    characters=characters
                )
                specs.append(spec)
            
            return specs

    def get_scene_metadata(self, scene_id: str) -> Optional[Dict]:
        """Get a summary of metadata for a scene including title, importance, and character count"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get basic scene data
            cursor.execute("""
                SELECT title, importance, description,
                       (SELECT COUNT(*) FROM scene_characters WHERE scene_id = scenes.scene_id) as character_count
                FROM scenes 
                WHERE scene_id = ?
            """, (scene_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return {
                'scene_id': scene_id,
                'title': row['title'],
                'importance': row['importance'],
                'description': row['description'],
                'character_count': row['character_count'],
                'has_analysis': self.get_scene_analysis_by_id(scene_id) is not None,
                'has_visual_plan': self.get_visual_plan_by_id(scene_id) is not None,
                'shot_spec_count': len(self.get_shot_specs_by_scene_id(scene_id))
            } 