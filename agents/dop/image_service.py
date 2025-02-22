import asyncio
import fal_client
from agents.dop.models.scene import CharacterDescription, ScenePanel
import aiohttp
import re
import os
import json
from datetime import datetime

# Define output directory structure
OUTPUT_DIR = "output"
IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")
METADATA_DIR = os.path.join(OUTPUT_DIR, "metadata")

def setup_output_directories():
    """Create output directories if they don't exist."""
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(METADATA_DIR, exist_ok=True)
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_metadata(character: CharacterDescription, image_path: str, session_id: str, index: int):
    """Save character metadata and generation details to JSON."""
    metadata = {
        "character": character.dict(),
        "generation": {
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "session_id": session_id,
            "character_index": index
        }
    }
    
    metadata_path = os.path.join(METADATA_DIR, f"character_{index}_{character.name.lower()}_{session_id}.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    return metadata_path

def parse_characters_from_prompt(prompt: str) -> list[CharacterDescription]:
    """Extract character descriptions from a prompt and convert them to CharacterDescription objects."""
    characters = []
    
    # Example prompt pattern matching (can be enhanced based on prompt structure)
    character_blocks = re.split(r'\d+\)', prompt)  # Split on numbered lists
    character_blocks = [b.strip() for b in character_blocks if b.strip()]
    
    for block in character_blocks:
        try:
            # Extract name (assuming format: "Name: description" or "Name is...")
            name_match = re.search(r'([A-Za-z]+)(?::|is|\s*,)', block)
            if not name_match:
                continue
            name = name_match.group(1).strip()
            
            # Basic attribute extraction (can be enhanced)
            physical = {
                "build": extract_attribute(block, r'(slender|athletic|rugged|compact|tall|short|thin|muscular)'),
                "height": extract_attribute(block, r'(tall|short|average|petite)'),
                "hair": extract_attribute(block, r'hair[^,\.]+'),
                "eyes": extract_attribute(block, r'eyes?[^,\.]+'),
                "skin": extract_attribute(block, r'skin[^,\.]+') or "not specified"
            }
            
            clothing = {
                "outfit": extract_attribute(block, r'wearing[^,\.]+') or "steampunk attire",
                "accessories": extract_attribute(block, r'accessories?[^,\.]+') or "typical steampunk accessories",
                "details": extract_attribute(block, r'details?[^,\.]+') or "standard details"
            }
            
            demeanor = {
                "posture": extract_attribute(block, r'posture[^,\.]+') or "neutral",
                "movement": extract_attribute(block, r'move(?:ment|s)[^,\.]+') or "standard",
                "expression": extract_attribute(block, r'expression[^,\.]+') or "neutral"
            }
            
            character = CharacterDescription(
                name=name,
                age="adult",  # Default if not specified
                gender="unspecified",  # Default if not specified
                physical_appearance=physical,
                clothing=clothing,
                demeanor=demeanor
            )
            characters.append(character)
            
        except Exception as e:
            print(f"Failed to parse character block: {e}")
            continue
    
    return characters

def extract_attribute(text: str, pattern: str) -> str:
    """Extract an attribute from text using regex pattern."""
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0).strip() if match else ""

async def generate_character_image(characters: list[CharacterDescription], index: int, session_id: str, scene_prompt: str = None, shot_id: str = None) -> None:
    try:
        # Create a merged prompt that includes both scene and character details
        if scene_prompt:
            # Get all character names for the scene
            character_names = [char.name for char in characters]
            if len(character_names) > 1:
                prompt = (
                    f"A detailed scene showing {scene_prompt}. "
                    f"The scene includes {', '.join(character_names[:-1])} and {character_names[-1]} interacting naturally. "
                    "The image should be photorealistic, with professional studio lighting, "
                    "high detail, and cinematic composition. "
                    "All characters should be clearly visible and well-integrated into the scene, "
                    "with their positions and interactions matching their described demeanors."
                )
            else:
                prompt = (
                    f"A detailed scene showing {scene_prompt}. "
                    "The image should be photorealistic, with professional studio lighting, "
                    "high detail, and cinematic composition. "
                    "The character should be clearly visible and well-integrated into the scene, "
                    "with their positions and interactions matching their described demeanors."
                )
        else:
            # For single character portraits, use the first character
            if len(characters) >= 1:
                character = characters[0]
                prompt = (
                    f"Full body portrait of {character.name} in a steampunk setting. "
                    f"Physical features: {character.physical_appearance['build']}, {character.physical_appearance['height']}, "
                    f"{character.physical_appearance['hair']}, {character.physical_appearance['eyes']}, "
                    f"{character.physical_appearance['skin']}. "
                    f"Wearing {character.clothing['outfit']}, {character.clothing['accessories']}, {character.clothing['details']}. "
                    f"Their demeanor shows {character.demeanor['posture']}, with {character.demeanor['movement']} movements "
                    f"and {character.demeanor['expression']}. "
                    "Detailed steampunk environment with brass and copper machinery in background. "
                    "Professional studio lighting with atmospheric steam effects."
                )

        print(f"\n🎭 Generating {'scene' if scene_prompt else 'image for Character'} {index}")
        print("\n📝 Generated Prompt:")
        print(prompt)
        
        # Submit the image generation request
        handler = await fal_client.submit_async(
            "fal-ai/flux-pro/v1.1-ultra",
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "aspect_ratio": "4:5",  # Keep original aspect ratio
                "enable_safety_checker": True,
                "safety_tolerance": "2",
                "output_format": "jpeg",
                "raw": False
            }
        )

        print(f"\n📋 Request ID: {handler.request_id}")

        # Wait for and process the result
        async for event in handler.iter_events(with_logs=True):
            if isinstance(event, dict) and event.get("status") == "error":
                raise Exception(event.get("message", "Unknown error during generation"))
            elif isinstance(event, dict) and event.get("status") == "completed":
                print(f"\n✅ Generation completed!")

        # Get the final result
        result = await handler.get()
        
        if result and result.get("images"):
            # Save the generated image
            image_url = result["images"][0]["url"]
            print(f"\n🖼️ Image URL generated")
            
            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        # Create filename with session ID
                        if scene_prompt:
                            # For scenes, include all character names in filename
                            char_names = "_".join(char.name.lower() for char in characters)
                            filename = f"{shot_id}.jpg"
                        else:
                            # For individual portraits
                            filename = f"character_{index}_{characters[0].name.lower()}_{session_id}.jpg"
                        
                        image_path = os.path.join(IMAGE_DIR, filename)
                        
                        # Save image
                        with open(image_path, 'wb') as f:
                            f.write(await resp.read())
                        print(f"\n💾 Image saved as: {image_path}")
                        
                        # Save metadata for all characters in the scene
                        metadata_paths = []
                        for i, char in enumerate(characters):
                            metadata_path = save_metadata(char, image_path, session_id, i + 1)
                            metadata_paths.append(metadata_path)
                        print(f"📄 Metadata saved for all characters: {', '.join(metadata_paths)}")
        else:
            print(f"\n❌ No images generated")

    except Exception as e:
        print(f"\n❌ An error occurred while generating image: {str(e)}")

async def generate_test_image(scene_panel: ScenePanel = None):
    # Setup output directories and get session ID
    session_id = setup_output_directories()
    print(f"🆔 Session ID: {session_id}")
    print(f"📁 Output directories created at {OUTPUT_DIR}")

    # Get characters from the storyboard database
    from agents.story_boarder.storage import StoryboardStorage
    storage = StoryboardStorage()
    db_characters = storage.db.load_script_characters()
    
    # Convert database characters to CharacterDescription objects
    characters = []
    for char in db_characters:
        # Initialize empty dictionaries for required attributes
        physical = {"build": "", "height": "", "hair": "", "eyes": "", "skin": ""}
        clothing = {"outfit": "", "accessories": "", "details": ""}
        demeanor = {"posture": "", "movement": "", "expression": ""}
        
        # Extract physical attributes if they exist in traits or description
        for attr in ['build', 'height', 'hair', 'eyes', 'skin']:
            value = extract_attribute(char['traits'], f"{attr}[^,\.]+") or extract_attribute(char['description'], f"{attr}[^,\.]+")
            if value:
                physical[attr] = value
                
        # Extract clothing details if they exist
        for attr in ['outfit', 'accessories', 'details']:
            value = extract_attribute(char['description'], f"{attr}[^,\.]+")
            if value:
                clothing[attr] = value
                
        # Extract demeanor if it exists
        for attr in ['posture', 'movement', 'expression']:
            value = extract_attribute(char['traits'], f"{attr}[^,\.]+") or extract_attribute(char['description'], f"{attr}[^,\.]+")
            if value:
                demeanor[attr] = value
        
        # Create character with required fields
        character = CharacterDescription(
            name=char['name'],
            age="adult",  # Required field
            gender="unspecified",  # Required field
            physical_appearance=physical,  # Required field
            clothing=clothing,  # Required field
            demeanor=demeanor  # Required field
        )
        characters.append(character)
    
    print(f"\n🎭 Found {len(characters)} characters in the database")
    
    # make scene panel character focus objects lower case and also remove quotes
    character_focus = [char.lower().replace('"', '').replace("“", "").replace("”", "") for char in scene_panel.character_focus]

    # Filter characters to only those in the scene
    scene_characters = [char for char in characters if char.name.lower().replace('"', '').replace("“", "").replace("”", "") in character_focus]
    # Create a detailed scene description with characters
    scene_description = f"{scene_panel.description} "
    
    # Add visual style details
    scene_description += f"The scene has {', '.join(f'{k}: {v}' for k, v in scene_panel.visuals.items())}. "
    
    # Add camera angle
    scene_description += f"Shot from a {scene_panel.camera_angle.value} angle. "
    
    # Add character descriptions
    for char in scene_characters:
        scene_description += (
            f"{char.name} is present in the scene, "
            f"a {char.physical_appearance['build'] or 'person'} with "
            f"{char.physical_appearance['hair'] or 'natural hair'}, "
            f"{char.physical_appearance['eyes'] or 'eyes'}, and "
            f"{char.physical_appearance['skin'] or 'skin'}. "
            f"They are wearing {char.clothing['outfit'] or 'appropriate attire'}"
        )
        if char.clothing['accessories']:
            scene_description += f" with {char.clothing['accessories']}"
        if char.clothing['details']:
            scene_description += f", {char.clothing['details']}"
        scene_description += ". "
        
        scene_description += (
            f"Their demeanor shows {char.demeanor['posture'] or 'natural posture'}, "
            f"with {char.demeanor['movement'] or 'natural'} movements and "
            f"{char.demeanor['expression'] or 'neutral'} expression. "
        )
    
    print(f"\n📝 Generated Scene Description:")
    print(scene_description)
    
    # Generate the scene image with all characters
    await generate_character_image(
        characters=scene_characters,
        index=1,
        session_id=session_id,
        scene_prompt=scene_description,
        shot_id=scene_panel.panel_id
    )

    print(f"\n✨ Generation session completed!")
    print(f"📁 Images saved in: {IMAGE_DIR}")
    print(f"📄 Metadata saved in: {METADATA_DIR}")
