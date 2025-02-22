import argparse
import json
import sys
from pathlib import Path
import modal
from models.scene import ScenePanel
import time

def generate_image(
    description: str,
    output_dir: str = None,
    size: tuple = (1024, 1024),
    camera_angle: str = "wide",
    lighting: str = "natural daylight"
) -> dict:
    """Generate an image using the Modal image generation service."""
    # Setup output directory
    output_dir = Path(output_dir or Path.home() / "hitchcock_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create scene
    scene = ScenePanel(
        panel_id=f"scene_{int(time.time())}",
        description=description,
        visuals={
            "lighting": lighting,
            "colors": "natural, vibrant",
            "key_elements": "detailed composition, high quality",
            "mood": "atmospheric"
        },
        camera_angle=camera_angle,
        character_focus=[]
    )

    try:
        print(f"Connecting to Modal service...")
        text_to_image = modal.Function.from_name("hitchcock-image", "text_to_image")
        
        print(f"Generating image...")
        result = text_to_image.remote(
            scene=scene,
            character_specs={},
            size=size,
            num_images=1
        )
        
        # Get the generated image
        filename = f"scene_{scene.panel_id}.png"
        local_path = output_dir / filename
        
        # Copy from Modal volume to local directory
        with modal.Volume.from_name("hitchcock-output") as output_volume:
            output_volume.copy_file_from(filename, str(local_path))
        
        return {
            "output": str(local_path),
            "size": f"{size[0]}x{size[1]}",
            "description": description,
            "camera_angle": camera_angle,
            "lighting": lighting,
            "metadata": result.generation_metadata
        }

    except Exception as e:
        print(f"Error generating image: {str(e)}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Hitchcock Image Generator Client")
    parser.add_argument("description", type=str, help="Description of the scene to generate")
    parser.add_argument("--output", "-o", type=str, help="Output directory for generated images")
    parser.add_argument("--width", "-W", type=int, default=1024, help="Image width")
    parser.add_argument("--height", "-H", type=int, default=1024, help="Image height")
    parser.add_argument("--angle", "-a", type=str, default="wide", help="Camera angle")
    parser.add_argument("--lighting", "-l", type=str, default="natural daylight", help="Lighting condition")
    parser.add_argument("--json", "-j", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    result = generate_image(
        description=args.description,
        output_dir=args.output,
        size=(args.width, args.height),
        camera_angle=args.angle,
        lighting=args.lighting
    )

    if args.json:
        print(json.dumps(result, indent=4))
    else:
        print(f"\nImage generated successfully!")
        print(f"Output: {result['output']}")
        print(f"Size: {result['size']}")
        print(f"\nGeneration settings:")
        print(f"  Description: {result['description']}")
        print(f"  Camera Angle: {result['camera_angle']}")
        print(f"  Lighting: {result['lighting']}")
        print(f"\nMetadata:")
        for key, value in result['metadata'].items():
            print(f"  {key}: {value}")

if __name__ == "__main__":
    main() 