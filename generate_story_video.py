import asyncio
from datetime import datetime
from services.video import VideoService
from models.scene import ScenePanel, CameraAngle, CharacterDescription
import json
import os
from pathlib import Path

async def load_character_data(metadata_path: str) -> CharacterDescription:
    """Load character data from metadata file."""
    with open(metadata_path, 'r') as f:
        data = json.load(f)
        return CharacterDescription(**data["character"])

async def verify_image_path(path: str) -> bool:
    """Verify that an image file exists and is accessible."""
    try:
        path = Path(path)
        if not path.exists():
            print(f"⚠️ Image not found: {path}")
            return False
        if not path.is_file():
            print(f"⚠️ Not a file: {path}")
            return False
        if path.stat().st_size == 0:
            print(f"⚠️ Empty file: {path}")
            return False
        return True
    except Exception as e:
        print(f"⚠️ Error checking image {path}: {str(e)}")
        return False

async def main():
    # Initialize service
    video_service = VideoService()
    
    # Generate session ID
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"🆔 Session ID: {session_id}")

    # Define scene
    scene = ScenePanel(
        panel_id="scene_001",
        description="explores a vast steampunk laboratory filled with whirring machines and floating gears",
        visuals={
            "lighting": "Warm copper tones with steam effects",
            "colors": "Rich browns and metallic accents",
            "key_elements": "Steam-powered machinery, floating gears, brass instruments"
        },
        camera_angle=CameraAngle.WIDE,
        character_focus=["gears", "shouldered", "picks", "tall", "muscular"]
    )

    # Character image paths (from previous generation)
    base_path = Path(os.getcwd())
    character_images = {
        "gears": str(base_path / "output/images/character_1_gears_20250222_184950.jpg"),
        "shouldered": str(base_path / "output/images/character_2_shouldered_20250222_184950.jpg"),
        "picks": str(base_path / "output/images/character_3_picks_20250222_184950.jpg"),
        "tall": str(base_path / "output/images/character_4_tall_20250222_184950.jpg"),
        "muscular": str(base_path / "output/images/character_5_muscular_20250222_184950.jpg")
    }

    # Verify all images exist and are accessible
    valid_images = {}
    for role, path in character_images.items():
        if await verify_image_path(path):
            valid_images[role] = path
        else:
            print(f"⚠️ Skipping {role} due to invalid image path")

    if not valid_images:
        print("❌ No valid image files found!")
        return

    # Load character data
    characters = {}
    for role, image_path in valid_images.items():
        try:
            # Extract index from image path
            index = int(Path(image_path).stem.split('character_')[1].split('_')[0])
            metadata_path = f"output/metadata/character_{index}_{role}_{session_id}.json"
            
            if os.path.exists(metadata_path):
                characters[role] = await load_character_data(metadata_path)
            else:
                print(f"⚠️ Warning: Metadata file not found for {role}")
                # Create a basic character description if metadata is missing
                characters[role] = CharacterDescription(
                    name=role.capitalize(),
                    age="adult",
                    gender="unspecified",
                    physical_appearance={
                        "build": "average",
                        "height": "average",
                        "hair": "not specified",
                        "eyes": "not specified",
                        "skin": "not specified"
                    },
                    clothing={
                        "outfit": "steampunk attire",
                        "accessories": "typical steampunk accessories",
                        "details": "standard details"
                    },
                    demeanor={
                        "posture": "neutral",
                        "movement": "standard",
                        "expression": "neutral"
                    }
                )
        except Exception as e:
            print(f"⚠️ Error loading character {role}: {str(e)}")
            continue

    if not characters:
        print("❌ No valid characters found!")
        return

    print(f"\n🎭 Processing {len(characters)} characters with valid images...")

    # Process scene and generate video
    try:
        result = await video_service.process_scene(
            scene=scene,
            characters=characters,
            character_images=valid_images,
            session_id=session_id
        )

        if result:
            print(f"\n✨ Final video generated successfully!")
            print(f"📁 Video saved at: {result.storage_path}")
            
            # Save scene metadata
            metadata = {
                "scene": scene.dict(),
                "generation": {
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "character_count": len(characters),
                    "video_path": result.storage_path,
                    "processed_characters": list(characters.keys())
                }
            }
            
            metadata_path = os.path.join("output/metadata", f"scene_{scene.panel_id}_{session_id}.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"📄 Scene metadata saved at: {metadata_path}")
        else:
            print("\n❌ Failed to generate final video")
    
    except Exception as e:
        print(f"\n❌ Error during video generation: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting video generation process...")
    asyncio.run(main())
