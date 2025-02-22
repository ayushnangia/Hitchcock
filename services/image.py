from pathlib import Path
from typing import Dict, List, Tuple
import modal
import torch
from diffusers import (
    StableDiffusionXLPipeline,
    StableDiffusionXLImg2ImgPipeline,
    AutoencoderKL,
    EulerDiscreteScheduler,
    UniPCMultistepScheduler
)
from models import (
    ScenePanel,
    CharacterDescription,
    AssetResult,
    AssetType
)
from config import settings

# Initialize Modal app and define constants
TIMEOUT = 60 * 30  # 30 minutes
MODEL_DIR = "/model"
OUTPUT_DIR = "/output"
CACHE_DIR = "/cache"

# Create the Modal app
app = modal.App("hitchcock-image")

# Create persistent volumes
model_volume = modal.Volume.from_name("hitchcock-model", create_if_missing=True)
output_volume = modal.Volume.from_name("hitchcock-output", create_if_missing=True)
cache_volume = modal.Volume.from_name("hitchcock-cache", create_if_missing=True)

# Define the container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install(["libgl1-mesa-glx", "libglib2.0-0"])  # System dependencies
    .pip_install(
        "torch",
        "diffusers",
        "transformers",
        "accelerate",
        "safetensors",
        "xformers",
        "invisible-watermark>=0.2.0",
        "pydantic",
        "pydantic-settings"
    )
    .env({
        "HF_HOME": CACHE_DIR,
        "HUGGING_FACE_HUB_CACHE": CACHE_DIR,
        "TRANSFORMERS_CACHE": f"{CACHE_DIR}/transformers",
        "TORCH_HOME": f"{CACHE_DIR}/torch",
        "DIFFUSERS_CACHE": f"{CACHE_DIR}/diffusers"
    })
)

@app.cls(
    image=image,
    gpu="A100:4",
    volumes={
        MODEL_DIR: model_volume,
        OUTPUT_DIR: output_volume,
        CACHE_DIR: cache_volume
    },
    timeout=TIMEOUT
)
class ImageGenerator:
    def __enter__(self):
        """Initialize resources when entering the context."""
        model_volume.reload()
        cache_volume.reload()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup resources when exiting the context."""
        if hasattr(self, 'pipe'):
            del self.pipe
            if hasattr(self, 'refiner'):
                del self.refiner
            torch.cuda.empty_cache()

    @modal.enter()
    def initialize_model(self):
        """Initialize the model when the container starts."""
        try:
            # Use UniPC scheduler for better quality and speed
            scheduler = UniPCMultistepScheduler.from_config({
                "beta_start": settings.model.beta_start,
                "beta_end": settings.model.beta_end,
                "beta_schedule": settings.model.beta_schedule,
                "timestep_spacing": settings.model.timestep_spacing,
                "steps_offset": settings.model.steps_offset
            })

            # Load improved VAE
            vae = AutoencoderKL.from_pretrained(
                "madebyollin/sdxl-vae-fp16-fix",
                torch_dtype=torch.float16,
                use_safetensors=True
            )

            # Load base model with optimizations
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                vae=vae,
                scheduler=scheduler,
                cache_dir=MODEL_DIR,
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True
            ).to("cuda")

            # Load refiner for enhanced details
            self.refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-refiner-1.0",
                cache_dir=MODEL_DIR,
                torch_dtype=torch.float16,
                variant="fp16",
                use_safetensors=True
            ).to("cuda")

            # Enable optimizations
            self.pipe.enable_vae_tiling()
            self.pipe.enable_xformers_memory_efficient_attention()
            self.refiner.enable_vae_tiling()
            self.refiner.enable_xformers_memory_efficient_attention()
            
            if settings.model.enable_cpu_offload:
                self.pipe.enable_model_cpu_offload()
                self.refiner.enable_model_cpu_offload()

        except Exception as e:
            raise RuntimeError(f"Failed to initialize model: {str(e)}")

    def _generate_prompt(
        self,
        scene: ScenePanel,
        characters: Dict[str, CharacterDescription]
    ) -> str:
        """Generate a detailed prompt for the image generation model."""
        character_descriptions = []
        for char_name in scene.character_focus:
            if char_name in characters:
                char = characters[char_name]
                desc = (
                    f"{char.name}: {char.physical_appearance.get('build', '')} "
                    f"with {char.physical_appearance.get('hair', '')} hair, "
                    f"wearing {char.clothing.get('outfit', '')}, "
                    f"{char.demeanor.get('posture', '')}"
                )
                character_descriptions.append(desc)
        
        prompt = (
            f"{scene.description} "
            f"Camera angle: {scene.camera_angle}, "
            f"Lighting: {scene.visuals.get('lighting', '')}, "
            f"Characters: {', '.join(character_descriptions)}"
        )
        return prompt.strip()

    @modal.method()
    def generate_image(
        self,
        scene: ScenePanel,
        characters: Dict[str, CharacterDescription],
        output_path: str,
        size: Tuple[int, int] = None,
        num_images: int = 1
    ) -> AssetResult:
        """Generate an image for a specific scene panel."""
        try:
            # Set default size if not provided
            if size is None:
                size = (
                    settings.model.default_image_width,
                    settings.model.default_image_height
                )

            # Generate prompt
            prompt = self._generate_prompt(scene, characters)
            negative_prompt = (
                "blurry, low quality, distorted, deformed, ugly, duplicate, "
                "morbid, mutilated, poorly drawn face, bad anatomy, extra limbs"
            )

            # First pass with base model
            base_output = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=40,
                guidance_scale=7.5,
                width=size[0],
                height=size[1],
                num_images_per_prompt=num_images,
                output_type="latent"
            )

            # Refine the output
            refined_output = self.refiner(
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=30,
                guidance_scale=7.5,
                image=base_output.images,
                strength=0.3
            )

            # Save image to volume
            image = refined_output.images[0]
            filename = f"{scene.panel_id}.png"
            output_path = Path(OUTPUT_DIR) / filename
            image.save(str(output_path))
            output_volume.commit()

            return AssetResult(
                scene_id=scene.panel_id,
                asset_type=AssetType.IMAGE,
                storage_path=str(output_path),
                generation_metadata={
                    "model_version": "SDXL-1.0 + Refiner",
                    "base_steps": "40",
                    "refiner_steps": "30",
                    "guidance_scale": "7.5",
                    "refiner_strength": "0.3",
                    "vae": "sdxl-vae-fp16-fix",
                    "scheduler": "UniPC",
                    "size": f"{size[0]}x{size[1]}",
                    "prompt": prompt
                }
            )

        except Exception as e:
            raise RuntimeError(f"Image generation failed: {str(e)}")

@app.function(
    image=image,
    volumes={OUTPUT_DIR: output_volume},
    timeout=300  # 5 minutes
)
def text_to_image(
    scene: ScenePanel,
    character_specs: Dict[str, CharacterDescription],
    size: tuple[int, int] = (1024, 1024),
    num_images: int = 1
) -> AssetResult:
    """Generate an image from a scene description."""
    with ImageGenerator() as generator:
        return generator.generate_image.remote(
            scene=scene,
            characters=character_specs,
            output_path=f"scene_{scene.panel_id}.png",
            size=size,
            num_images=num_images
        )
