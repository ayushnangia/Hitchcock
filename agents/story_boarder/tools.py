from typing import Dict, List
import instructor
from openai import OpenAI
from agents.story_boarder.storage import StoryboardStorage
from pathlib import Path
from .models import ScriptScene, Shot, SceneAnalysis, VisualPlan, ShotImageSpec

# Initialize storage
storage = StoryboardStorage()

def plan_storyboard_scenes() -> str:
    """
    Break down script into scenes and identify important ones to storyboard.
    Saves scenes to storage instead of returning them.
    """
    # get script text from file
    with open("data/script_writer/script.txt", "r") as f:
        script_text = f.read()

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
            model="gpt-4o-mini",
            response_model=List[ScriptScene],
            messages=[
                {"role": "system", "content": "You are a professional script analyst breaking down scripts into structured scene information."},
                {"role": "user", "content": prompt}
            ]
        )
        # Save scenes to storage
        storage.save_scenes(response)
        
    except Exception as e:
        print(f"Error analyzing script: {e}")
        # Save minimal scene list as fallback
        fallback_scenes = [
            ScriptScene(
                scene_id="error_001",
                title="Error Processing Scene",
                script_text=script_text[:100] + "...",  # First 100 chars
                importance="medium",
                characters=["Unknown"],
                description="Error occurred during scene analysis"
            )
        ]
        storage.save_scenes(fallback_scenes)

    return f"I have saved {len(response)} scenes to the database"

def analyze_script_scenes() -> str:
    """
    Analyze scenes to identify key moments and plan shots.
    Loads scenes from storage and saves analyses back to storage.
    """
    client = instructor.patch(OpenAI())
    analyses = []
    
    # Load scenes from storage
    scenes = storage.load_scenes()

    for scene in scenes:
        # if scene.importance in ["critical", "high"]:  # Only analyze important scenes
        if True:
            # Create prompt for scene analysis
            prompt = f"""
            Analyze this scene and break it down into key moments and shots. The scene information is:
            
            Title: {scene.title}
            Description: {scene.description}
            Characters: {', '.join(scene.characters)}
            Scene ID: {scene.scene_id}
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
                    model="gpt-4o-mini",
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

    # Save analyses to storage
    storage.save_scene_analyses(analyses)

    return f"I have saved {len(analyses)} scene analyses to the database"

def plan_visual_elements() -> str:
    """
    Plan visual elements for each scene based on their analysis.
    Loads scene analyses from storage and saves visual plans back to storage.
    """
    client = instructor.patch(OpenAI())
    visual_plans = []
    
    # Load scene analyses from storage
    scene_analyses = storage.load_scene_analyses()

    for analysis in scene_analyses:
        prompt = f"""
        Plan the visual elements for this scene:
        Setting: {analysis.setting}
        Mood: {analysis.mood}
        Time of Day: {analysis.time_of_day}
        Scene ID: {analysis.scene_id}
        
        Create a visual plan with:
        1. Lighting setup appropriate for the setting and mood
        2. Key props needed for the scene
        3. Overall atmosphere description
        4. Any special effects needed
        """

        try:
            plan = client.chat.completions.create(
                model="gpt-4o-mini",
                response_model=VisualPlan,
                messages=[
                    {"role": "system", "content": "You are a cinematographer planning visual elements for film scenes."},
                    {"role": "user", "content": prompt}
                ]
            )
            visual_plans.append(plan)
        except Exception as e:
            print(f"Error planning visuals for scene {analysis.scene_id}: {e}")
            fallback = VisualPlan(
                scene_id=analysis.scene_id,
                lighting=f"Standard {analysis.time_of_day} lighting",
                props=["Basic set dressing"],
                atmosphere=analysis.mood,
                special_effects=[]
            )
            visual_plans.append(fallback)

    # Save visual plans to storage
    storage.save_visual_plans(visual_plans)

    return f"I have saved {len(visual_plans)} visual plans to the database"

def create_shot_image_specs() -> str:
    """
    Creates and saves comprehensive specifications for image generation for each shot.
    Combines scene, analysis, and visual plan information to generate detailed shot specs.
    Saves the specs to storage for use by the image generation agent.
    """
    # Load all necessary data
    scenes = storage.load_scenes()
    analyses = storage.load_scene_analyses()
    visual_plans = storage.load_visual_plans()
    
    # Create a lookup dictionary for scenes and visual plans
    scene_dict = {scene.scene_id: scene for scene in scenes}
    visual_plan_dict = {plan.scene_id: plan for plan in visual_plans}
    
    shot_specs = []
    
    # Process each scene analysis
    for analysis in analyses:
        scene = scene_dict.get(analysis.scene_id)
        visual_plan = visual_plan_dict.get(analysis.scene_id)
        
        if not scene or not visual_plan:
            continue
            
        # Process each shot in the scene
        for i, shot in enumerate(analysis.shots):
            # Create a unique shot ID
            shot_id = f"{analysis.scene_id}_shot_{i+1}"
            
            # Combine descriptions for more context
            combined_description = f"Scene: {scene.description}\nShot: {shot.description}"
            
            # Create the shot specification
            spec = ShotImageSpec(
                scene_id=analysis.scene_id,
                shot_id=shot_id,
                description=combined_description,
                camera_specs={
                    "type": shot.camera,
                    "movement": shot.camera_movement,
                    "focus": shot.focus
                },
                visual_elements={
                    "lighting": visual_plan.lighting,
                    "atmosphere": visual_plan.atmosphere,
                    "time_of_day": analysis.time_of_day
                },
                props=visual_plan.props,
                special_effects=visual_plan.special_effects,
                characters=scene.characters
            )
            shot_specs.append(spec)
    
    # Save the shot specs to storage
    storage.save_shot_image_specs(shot_specs)
    return f"I have saved {len(shot_specs)} shot image specifications to the database"

def critique_generated_images() -> str:
    """
    Review the generated images in the output directory and provide feedback.
    For now, returns a simple approval message.
    
    Returns:
        A string message with the critique/feedback.
    """
    output_dir = Path.home() / "hitchcock_output"
    
    # For now, just return an approval message
    # TODO: Implement actual image analysis and critique
    return "I like it, go ahead, no changes needed"

tools = [
    {
        "tool": {
            "type": "function",
            "function": {
                "name": "plan_storyboard_scenes",
                "description": "Break down script into scenes and identify important ones",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
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
                    "properties": {},
                    "required": []
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
                    "properties": {},
                    "required": []
                }
            }
        },
        "function": plan_visual_elements,
    },
    {
        "tool": {
            "type": "function",
            "function": {
                "name": "create_shot_image_specs",
                "description": "Create and save comprehensive specifications for generating images for each shot",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        "function": create_shot_image_specs,
    },
    {
        "tool": {
            "type": "function",
            "function": {
                "name": "critique_generated_images",
                "description": "Review and critique the generated storyboard images after the DOP prompts you.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        "function": critique_generated_images,
    }
]
