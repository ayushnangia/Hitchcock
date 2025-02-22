import asyncio
import fal_client
from models.scene import CharacterDescription
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

async def generate_character_image(character: CharacterDescription, index: int, session_id: str) -> None:
    try:
        # Create individual character prompt
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

        print(f"\n🎭 Generating image for Character {index}: {character.name}")
        print("\n📝 Generated Prompt:")
        print(prompt)
        
        # Submit the image generation request
        handler = await fal_client.submit_async(
            "fal-ai/flux-pro/v1.1-ultra",
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "aspect_ratio": "4:5",  # Portrait aspect ratio for character shots
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
                print(f"\n✅ Generation completed for {character.name}!")

        # Get the final result
        result = await handler.get()
        
        if result and result.get("images"):
            # Save the generated image
            image_url = result["images"][0]["url"]
            print(f"\n🖼️ Image URL for {character.name}: {image_url}")
            
            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        # Create filename with session ID
                        filename = f"character_{index}_{character.name.lower()}_{session_id}.jpg"
                        image_path = os.path.join(IMAGE_DIR, filename)
                        
                        # Save image
                        with open(image_path, 'wb') as f:
                            f.write(await resp.read())
                        print(f"\n💾 Image saved as: {image_path}")
                        
                        # Save metadata
                        metadata_path = save_metadata(character, image_path, session_id, index)
                        print(f"📄 Metadata saved as: {metadata_path}")
        else:
            print(f"\n❌ No images generated for {character.name}")

    except Exception as e:
        print(f"\n❌ An error occurred while generating {character.name}: {str(e)}")

async def generate_test_image():
    # Setup output directories and get session ID
    session_id = setup_output_directories()
    print(f"🆔 Session ID: {session_id}")
    print(f"📁 Output directories created at {OUTPUT_DIR}")

    # Rich character descriptions prompt
    test_prompt = """
    1) Isabella is a tall and graceful woman with olive skin and striking features. Her long raven hair is intricately braided with copper wires and brass gears, eyes are deep amber with mechanical iris implants. She wears a high-necked crimson leather coat with brass buttons and steam vents, accessorized with a brass monocle that displays holographic data and fingerless gloves with exposed mechanical joints. Her posture is elegant yet ready for action, movements are precise and calculated, with an expression of intense curiosity and determination.

    2) Magnus is a broad-shouldered, muscular man with weathered skin and burn scars. His silver-streaked dark hair is pulled back, revealing a brass plate at his temple, eyes are mechanical constructs glowing electric blue. He wears a heavy leather apron covered in tool pouches over a brass-plated vest, accessories include protective goggles with multiple lenses and a mechanical arm with built-in tools. His posture is powerful and grounded, movements are deliberate and strong, expression shows focused concentration with a hint of pride.

    3) Mei is a petite but athletic woman with porcelain skin marked with delicate gear tattoos. Her jet-black hair is styled in an elaborate updo held with jade and brass hairpins that double as lock picks, eyes are emerald green with golden flecks. She wears a modified qipao in midnight blue silk with brass armor panels, accessorized with a mechanical fan that conceals various tools and a belt of small potion vials. Her posture is fluid and balanced, movements are swift and graceful, expression is mysterious with a knowing smile.

    4) Thaddeus is a tall, lean man with dark umber skin that gleams with metallic undertones. His closely-cropped hair has patterns shaved into it revealing copper neural implants, eyes are gold with telescopic modifications. He wears an elaborate bronze-colored coat with multiple moving parts and gauges, accessories include a hovering mechanical familiar and chronometer rings on each finger. His posture is scholarly yet alert, movements are smooth and purposeful, expression shows analytical interest and gentle wisdom.

    5) Aurora is a muscular, athletic woman with frost-pale skin that seems to shimmer. Her white-blonde hair flows with static electricity and contains floating metallic ornaments, eyes are silver with clockwork patterns. She wears a form-fitting suit of articulated brass plates over a tesla-coil powered bodysuit, accessories include energy-conducting gauntlets and boots with magnetic soles. Her posture is dynamic and energetic, movements are bold and powerful, expression radiates confidence and excitement.
    """

    # Parse characters from the prompt
    characters = parse_characters_from_prompt(test_prompt)
    
    print(f"\n🎭 Found {len(characters)} characters in the prompt")
    
    # Generate images for each parsed character
    for i, character in enumerate(characters, 1):
        print(f"\n📝 Character {i} Details:")
        print(f"Name: {character.name}")
        print(f"Physical Appearance: {character.physical_appearance}")
        print(f"Clothing: {character.clothing}")
        print(f"Demeanor: {character.demeanor}")
        print("\n-----------------------------------")
        
        await generate_character_image(character, i, session_id)
        print("\n===================================\n")

    print(f"\n✨ Generation session completed!")
    print(f"📁 Images saved in: {IMAGE_DIR}")
    print(f"📄 Metadata saved in: {METADATA_DIR}")
