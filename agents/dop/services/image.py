import os
from typing import Dict, List
import asyncio
import fal_client
from models.scene import StoryboardRequest, ScenePanel
from models.assets import AssetResult, AssetType, ProcessingStatus, ProcessingResponse

class ImageService:
    def __init__(self, fal_key: str = None):
        """Initialize the FAL.ai image service."""
        self.fal_key = fal_key or os.getenv("FAL_KEY")
        if not self.fal_key:
            raise ValueError("FAL_KEY must be provided either through constructor or environment variable")
        
        os.environ["FAL_KEY"] = self.fal_key

    def _generate_prompt(self, panel: ScenePanel, characters: Dict) -> str:
        """Generate a detailed prompt for the image generation."""
        prompt = f"Camera angle: {panel.camera_angle.value}. {panel.description}"
        
        # Add character details
        for char_name in panel.character_focus:
            if char_name in characters:
                char = characters[char_name]
                prompt += f"\n{char.name}: {char.physical_appearance.get('description', '')}, "
                prompt += f"wearing {char.clothing.get('description', '')}, "
                prompt += f"{char.demeanor.get('expression', '')}"
        
        # Add visual details
        visuals = panel.visuals
        if visuals:
            prompt += f"\nVisual style: {', '.join(f'{k}: {v}' for k, v in visuals.items())}"
        
        return prompt

    def _get_aspect_ratio(self, camera_angle: str) -> str:
        """Determine the best aspect ratio based on camera angle."""
        wide_angles = {"wide", "birds_eye"}
        close_angles = {"close_up", "extreme_close_up"}
        
        if camera_angle in wide_angles:
            return "16:9"
        elif camera_angle in close_angles:
            return "4:3"
        return "3:2"  # Default balanced ratio

    async def generate_storyboard(self, request: StoryboardRequest) -> ProcessingResponse:
        """Generate images for a storyboard using FAL.ai FLUX Pro."""
        assets: List[AssetResult] = []
        error_log: List[str] = []

        for panel in request.panels:
            try:
                # Generate the prompt
                prompt = self._generate_prompt(panel, request.characters)
                aspect_ratio = self._get_aspect_ratio(panel.camera_angle.value)
                
                # Generate the image using FAL.ai FLUX Pro
                handler = await fal_client.submit_async(
                    "fal-ai/flux-pro/v1.1-ultra",
                    arguments={
                        "prompt": prompt,
                        "num_images": 1,
                        "enable_safety_checker": True,
                        "safety_tolerance": "2",
                        "output_format": "jpeg",
                        "aspect_ratio": aspect_ratio,
                        "raw": False  # Set to True for less processed, more natural look
                    }
                )

                # Wait for the result
                async for event in handler.iter_events(with_logs=True):
                    if isinstance(event, dict) and event.get("status") == "error":
                        raise Exception(event.get("message", "Unknown error during generation"))

                result = await handler.get()

                if result and result.get("images"):
                    # Store the result
                    asset = AssetResult(
                        scene_id=panel.panel_id,
                        asset_type=AssetType.IMAGE,
                        storage_path=result["images"][0]["url"],
                        generation_metadata={
                            "model": "fal-ai/flux-pro/v1.1-ultra",
                            "prompt": prompt,
                            "camera_angle": panel.camera_angle.value,
                            "aspect_ratio": aspect_ratio
                        }
                    )
                    assets.append(asset)
                else:
                    raise Exception("No images generated in the result")

            except Exception as e:
                error_log.append(f"Error generating panel {panel.panel_id}: {str(e)}")

        # Create the response
        status = ProcessingStatus.COMPLETED if not error_log else ProcessingStatus.FAILED
        return ProcessingResponse(
            request_id=request.panels[0].panel_id,  # Using first panel ID as request ID
            status=status,
            assets=assets,
            error_log=error_log if error_log else None
        )
