from pydantic_settings import BaseSettings, SettingsConfigDict

class ModelSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='HITCHCOCK_MODEL_',
        env_file='.env',
        extra='ignore'
    )
    
    # SDXL Configuration
    sdxl_model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"
    sdxl_vae_id: str = "madebyollin/sdxl-vae-fp16-fix"
    cache_dir: str = "/cache"
    torch_dtype: str = "float16"
    use_safetensors: bool = True
    
    # Generation Parameters
    default_image_width: int = 1024
    default_image_height: int = 1024
    num_inference_steps: int = 40
    guidance_scale: float = 8.0
    denoising_end: float = 0.8
    guidance_rescale: float = 0.7
    
    # Scheduler Parameters
    beta_start: float = 0.00085
    beta_end: float = 0.012
    beta_schedule: str = "scaled_linear"
    timestep_spacing: str = "leading"
    steps_offset: int = 1

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    model: ModelSettings = ModelSettings()
    debug: bool = False

# Create global settings instance
settings = Settings()
