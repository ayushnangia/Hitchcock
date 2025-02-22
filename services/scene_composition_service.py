import asyncio
import fal_client
from typing import Dict, List, Optional, Tuple, AsyncGenerator, Literal
import os
import json
from datetime import datetime
from models.scene import StoryboardRequest, ScenePanel, CharacterDescription, CameraAngle
from models.assets import AssetResult, AssetType
from PIL import Image
import io
import numpy as np
import cv2

# FAL.ai supported image sizes
ImageSize = Literal[
    "square_hd",
    "square",
    "portrait_4_3",
    "portrait_16_9",
    "landscape_4_3",
    "landscape_16_9"
]

class SceneCompositionService:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.images_dir = os.path.join(output_dir, "images")
        self.metadata_dir = os.path.join(output_dir, "metadata")
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

    def _get_image_size(self, camera_angle: CameraAngle) -> ImageSize:
        """Get appropriate image size based on camera angle."""
        # Map camera angles to appropriate aspect ratios
        size_map = {
            CameraAngle.WIDE: "landscape_16_9",
            CameraAngle.MEDIUM: "portrait_4_3",
            CameraAngle.CLOSE_UP: "portrait_4_3",
            CameraAngle.EXTREME_CLOSE_UP: "square_hd",
            CameraAngle.BIRDS_EYE: "landscape_16_9",
            CameraAngle.LOW_ANGLE: "portrait_4_3",
            CameraAngle.DUTCH_ANGLE: "landscape_16_9",
            CameraAngle.OVER_SHOULDER: "landscape_4_3"
        }
        return size_map.get(camera_angle, "square_hd")

    def _build_character_prompt(self, character: CharacterDescription) -> str:
        """Build a detailed prompt for a character."""
        return (
            f"{character.name}, {character.age} {character.gender}. "
            f"Physical appearance: {', '.join(f'{k}: {v}' for k, v in character.physical_appearance.items())}. "
            f"Wearing {', '.join(f'{k}: {v}' for k, v in character.clothing.items())}. "
            f"Demeanor shows {', '.join(f'{k}: {v}' for k, v in character.demeanor.items())}."
        )

    def _get_camera_angle_prompt(self, angle: CameraAngle) -> str:
        """Get camera angle specific prompts."""
        angle_prompts = {
            CameraAngle.WIDE: "A wide establishing shot showing the entire scene",
            CameraAngle.MEDIUM: "A medium shot from waist up",
            CameraAngle.CLOSE_UP: "A close-up shot focusing on the face and upper body",
            CameraAngle.EXTREME_CLOSE_UP: "An extreme close-up shot showing fine details",
            CameraAngle.BIRDS_EYE: "A high-angle birds-eye view looking down at the scene",
            CameraAngle.LOW_ANGLE: "A low-angle shot looking up at the subjects",
            CameraAngle.DUTCH_ANGLE: "A tilted dutch angle shot creating tension",
            CameraAngle.OVER_SHOULDER: "An over-the-shoulder shot showing perspective"
        }
        return angle_prompts.get(angle, "A balanced composition")

    def _build_scene_prompt(
        self,
        scene: ScenePanel,
        characters: Dict[str, CharacterDescription],
        visual_theme: Dict[str, str]
    ) -> Tuple[str, str]:
        """Build the main and negative prompts for the scene."""
        camera_prompt = self._get_camera_angle_prompt(scene.camera_angle)
        
        # Only use the scene description and camera angle since we're editing an existing image
        main_prompt = (
            f"{camera_prompt}. {scene.description}. "
            "Maintain consistent lighting and perspective."
        )
        
        negative_prompt = (
            "deformed, distorted, disfigured, poorly drawn, bad anatomy, wrong anatomy, "
            "extra limb, missing limb, floating limbs, disconnected limbs, mutation, mutated, "
            "ugly, disgusting, blurry, out of focus"
        )
        
        return main_prompt, negative_prompt

    def _create_and_upload_mask(self, image_path: str) -> Optional[str]:
        """Create a simple mask where white is the area to edit."""
        try:
            # Read image using OpenCV to get dimensions
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to read image: {image_path}")

            height, width = image.shape[:2]
            
            # Create a white mask
            mask = np.full((height, width), 255, dtype=np.uint8)
            
            # Calculate the rectangle size (center 60% of the image)
            rect_width = int(width * 0.6)
            rect_height = int(height * 0.6)
            x = (width - rect_width) // 2
            y = (height - rect_height) // 2
            
            # Draw black rectangle in the center (area to protect)
            cv2.rectangle(mask, (x, y), (x + rect_width, y + rect_height), 0, -1)
            
            # Save mask to temporary file
            temp_path = os.path.join(self.images_dir, "temp_mask.png")
            cv2.imwrite(temp_path, mask)
            
            # Upload to FAL.ai
            mask_url = fal_client.upload_file(temp_path)
            
            # Clean up
            os.remove(temp_path)
            
            return mask_url
        except Exception as e:
            print(f"Error creating mask: {str(e)}")
            return None

    async def _get_base_image(self, character_focus: List[str]) -> Optional[Tuple[str, str, int, int]]:
        """Get a suitable base image and create its mask from the output directory."""
        try:
            # List all image files in the output directory
            image_files = [f for f in os.listdir(self.images_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
            if not image_files:
                return None

            # Try to find an image matching a character in focus
            selected_file = None
            for char_id in character_focus:
                matching_images = [f for f in image_files if char_id.lower() in f.lower()]
                if matching_images:
                    selected_file = matching_images[0]
                    break

            # If no matching image found, use the first available image
            if not selected_file:
                selected_file = image_files[0]

            # Get full path and dimensions
            image_path = os.path.join(self.images_dir, selected_file)
            with Image.open(image_path) as img:
                width, height = img.size

            # Upload base image to FAL.ai
            image_url = fal_client.upload_file(image_path)
            
            # Create and upload mask
            mask_url = self._create_and_upload_mask(image_path)
            if not mask_url:
                return None
            
            return image_url, mask_url, width, height

        except Exception as e:
            print(f"Error getting base image: {str(e)}")
            return None

    async def generate_scene(
        self,
        scene: ScenePanel,
        characters: Dict[str, CharacterDescription],
        visual_theme: Dict[str, str]
    ) -> AsyncGenerator[dict, None]:
        """Generate a single scene image with streaming updates."""
        try:
            main_prompt, negative_prompt = self._build_scene_prompt(scene, characters, visual_theme)
            image_size = self._get_image_size(scene.camera_angle)
            
            print(f"\n🎨 Generating scene {scene.panel_id}")
            print("\n📝 Generated Prompt:")
            print(main_prompt)
            print(f"\n📐 Image Size: {image_size}")

            # Get base image and its mask
            base_image_result = await self._get_base_image(scene.character_focus)
            if not base_image_result:
                print("⚠️ No base image found or failed to create mask")
                yield {
                    "type": "error",
                    "message": "Failed to prepare base image and mask"
                }
                return

            base_image_url, mask_url, width, height = base_image_result
            print(f"\n🖼️ Using base image: {base_image_url}")
            print(f"🎭 Using edge-based mask: {mask_url}")

            # Submit the generation request
            handler = await fal_client.submit_async(
                "fal-ai/ideogram/v2/edit",
                arguments={
                    "prompt": main_prompt,
                    "image_url": base_image_url,
                    "mask_url": mask_url,
                    "style": "realistic",  # Using realistic style for better character rendering
                    "expand_prompt": True,  # Enable MagicPrompt for better prompt understanding
                }
            )

            # Process progress updates from the event stream
            async for event in handler.iter_events(with_logs=True):
                if isinstance(event, dict) and event.get("status") == "in-progress":
                    if "logs" in event:
                        for log in event["logs"]:
                            print(f"📋 {log['message']}")
                            yield {
                                "type": "progress",
                                "data": {"message": log["message"]}
                            }

            # Get the final result
            result = await handler.get()
            
            if result and isinstance(result, dict):
                # Extract image URL from the images array
                images = result.get("images", [])
                if images and len(images) > 0:
                    image_url = images[0].get("url")
                    if image_url:
                        # Save metadata
                        metadata = {
                            "scene_id": scene.panel_id,
                            "prompt": main_prompt,
                            "negative_prompt": negative_prompt,
                            "characters": list(characters.keys()),
                            "camera_angle": scene.camera_angle,
                            "image_size": image_size,
                            "base_image": base_image_url,
                            "timestamp": datetime.now().isoformat(),
                            "generation_params": {
                                "model": "fal-ai/ideogram/v2/edit",
                                "style": "realistic",
                                "expand_prompt": True,
                                "seed": result.get("seed")
                            }
                        }
                        
                        yield {
                            "type": "success",
                            "data": {
                                "scene_id": scene.panel_id,
                                "image_url": image_url,
                                "metadata": metadata
                            }
                        }
                    else:
                        print(f"Debug - No URL in image data: {json.dumps(images[0], indent=2)}")
                        yield {
                            "type": "error",
                            "message": "No image URL in the result"
                        }
                else:
                    print(f"Debug - No images in result: {json.dumps(result, indent=2)}")
                    yield {
                        "type": "error",
                        "message": "No images in the result"
                    }
            else:
                print(f"Debug - Invalid result type: {type(result)}")
                yield {
                    "type": "error",
                    "message": "Invalid response format from the model"
                }

        except Exception as e:
            yield {
                "type": "error",
                "message": f"Failed to generate scene {scene.panel_id}: {str(e)}"
            }

    async def generate_storyboard(self, request: StoryboardRequest) -> AsyncGenerator[dict, None]:
        """Generate all scenes for a storyboard with streaming updates."""
        print(f"\n🎬 Starting storyboard generation with {len(request.panels)} panels...")
        
        for panel in request.panels:
            async for event in self.generate_scene(
                scene=panel,
                characters=request.characters,
                visual_theme=request.visual_theme
            ):
                yield event

def create_scene_service(output_dir: str = "output") -> SceneCompositionService:
    """Factory function to create a scene service instance."""
    return SceneCompositionService(output_dir) 