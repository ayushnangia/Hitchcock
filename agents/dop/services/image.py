import modal
import torch
from PIL import Image
import io
import random
from pathlib import Path
from typing import Dict, Optional, Tuple
from models.scene import ScenePanel, CharacterDescription
from fastapi.responses import Response
from huggingface_hub import snapshot_download

# Constants
CACHE_PATH = "/model_cache"
OUTPUT_PATH = "/output_data"
MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
MINUTES = 60

def download_model():
    """Download model files into the image."""
    import torch
    from diffusers import AutoPipelineForText2Image
    
    # Download model files
    AutoPipelineForText2Image.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True
    )

# Create Modal app
app = modal.App("hitchcock-image")

# Create image with required dependencies
image = (modal.Image.debian_slim()
    .pip_install(
        "torch",
        "diffusers",
        "transformers",
        "accelerate",
        "safetensors",
        "pydantic",
        "fastapi",
        "huggingface-hub"
    )
    .run_function(download_model)
    # Add local source files last
    .add_local_python_source("models")
)

# Create volumes with create_if_missing to handle first run
cache_volume = modal.Volume.from_name("model-cache-vol", create_if_missing=True)
output_volume = modal.Volume.from_name("output-data-vol", create_if_missing=True)

@app.cls(
    image=image,
    gpu="A100",
    volumes={
        CACHE_PATH: cache_volume,
        OUTPUT_PATH: output_volume
    },
    timeout=10 * MINUTES
)
class ImageGenerator:
    @modal.enter()
    def enter(self):
        """Initialize the model when container starts."""
        import os
        from diffusers import AutoPipelineForText2Image
        
        # Create directories
        os.makedirs(CACHE_PATH, exist_ok=True)
        os.makedirs(OUTPUT_PATH, exist_ok=True)
        
        print("Initializing SDXL pipeline...")
        # Initialize pipeline
        self.pipeline = AutoPipelineForText2Image.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            cache_dir=CACHE_PATH
        ).to("cuda")
        
        print("Pipeline initialization complete!")

    def _construct_prompt(
        self,
        scene: ScenePanel,
        character_specs: Dict[str, CharacterDescription]
    ) -> Tuple[str, str]:
        """Construct the prompt and negative prompt from the scene and character specs."""
        # Base prompt from scene description
        prompt = scene.description

        # Add visual elements
        if scene.visuals:
            prompt += f", {scene.visuals.get('lighting', '')}"
            prompt += f", {scene.visuals.get('colors', '')}"
            prompt += f", {scene.visuals.get('key_elements', '')}"
            prompt += f", {scene.visuals.get('mood', '')}"

        # Add camera angle
        prompt += f", {scene.camera_angle.value} shot"

        # Add character details if specified
        for char_id in scene.character_focus:
            if char_id in character_specs:
                char = character_specs[char_id]
                prompt += f", {char.name} wearing {', '.join(char.clothing.values())}"
                prompt += f", {', '.join(char.physical_appearance.values())}"

        # Standard negative prompt for high quality output
        negative_prompt = "blurry, low quality, distorted, deformed, ugly, bad anatomy"

        return prompt, negative_prompt

    @modal.method()
    def generate(
        self,
        scene: ScenePanel,
        character_specs: Dict[str, CharacterDescription],
        size: Tuple[int, int] = (1024, 1024),
        num_images: int = 1,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        seed: int = None
    ) -> Dict:
        """Generate images from a scene description using SDXL"""
        try:
            # Set random seed if provided
            if seed is not None:
                torch.manual_seed(seed)
                print(f"Using seed: {seed}")
            
            # Construct the prompt
            prompt, negative_prompt = self._construct_prompt(scene, character_specs)
            print(f"Generated prompt: {prompt}")
            
            # Generate the image
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=size[0],
                height=size[1],
                num_images_per_prompt=num_images,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
            )
            
            # Save images and return metadata
            output_paths = []
            for idx, image in enumerate(result.images):
                filename = f"scene_{scene.panel_id}.png"
                if num_images > 1:
                    filename = f"scene_{scene.panel_id}_{idx}.png"
                
                filepath = str(Path(OUTPUT_PATH) / filename)
                image.save(filepath, format='PNG')
                output_paths.append(filename)
                print(f"Saved image: {filepath}")
                
                # Commit after each save to ensure no data loss
                output_volume.commit()
                
            # Clear CUDA cache to reduce memory fragmentation
            torch.cuda.empty_cache()
            
            return {
                "filenames": output_paths,
                "generation_metadata": {
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "size": f"{size[0]}x{size[1]}",
                    "num_inference_steps": num_inference_steps,
                    "guidance_scale": guidance_scale,
                    "seed": seed
                }
            }
        except Exception as e:
            print(f"Error during image generation: {str(e)}")
            raise

    @modal.web_endpoint(method="POST")
    def api(
        self,
        scene: ScenePanel,
        character_specs: Dict[str, CharacterDescription] = None,
        seed: int = None
    ):
        """Web endpoint for image generation"""
        try:
            print(f"Received API request for scene: {scene.panel_id}")
            result = self.generate.local(
                scene=scene,
                character_specs=character_specs or {},
                num_images=1,
                seed=seed
            )
            
            # Return the first generated image
            filepath = str(Path(OUTPUT_PATH) / result['filenames'][0])
            with open(filepath, "rb") as f:
                image_bytes = f.read()
            print(f"Returning generated image: {filepath}")
            return Response(content=image_bytes, media_type="image/png")
        except Exception as e:
            print(f"Error in API endpoint: {str(e)}")
            raise

@app.function(
    image=image,  # Use the same image with models source
    volumes={OUTPUT_PATH: output_volume}  # Only need output volume for this function
)
def text_to_image(
    scene: ScenePanel,
    character_specs: Dict[str, CharacterDescription] = None,
    size: Tuple[int, int] = (1024, 1024),
    num_images: int = 1,
    seed: int = None
) -> Dict:
    """Convenience function to generate images from a scene description."""
    generator = ImageGenerator()
    return generator.generate(
        scene=scene,
        character_specs=character_specs or {},
        size=size,
        num_images=num_images,
        seed=seed
    )
