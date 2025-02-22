from typing import List
import modal
from moviepy.editor import ImageClip, concatenate_videoclips
from models import (
    ScenePanel,
    AssetResult,
    AssetType
)

# Initialize Modal app
app = modal.App("hitchcock-video")

# Define video processing paths
VIDEO_PATH = "/videos"

# Create persistent volume for video processing
volume = modal.Volume.from_name("hitchcock-video", create_if_missing=True)

# Create base image with all dependencies
image = (modal.Image.debian_slim()
    .pip_install(
        "moviepy==1.0.3",
        "numpy==1.26.0",
        "pillow==10.2.0",
        "opencv-python-headless==4.9.0.80",
        "av==11.0.0"
    )
    .add_local_python_source("config", "models")
)

@app.cls(
    image=image,
    gpu=modal.gpu.A10G(),
    volumes={VIDEO_PATH: volume},
    timeout=3600,
    cpu=8
)
class VideoProcessor:
    def __enter__(self):
        """Initialize resources when the container starts."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when the container exits."""
        pass
    
    def apply_camera_movement(
        self,
        clip: ImageClip,
        scene: ScenePanel
    ) -> ImageClip:
        """Apply camera movements based on scene specifications."""
        try:
            duration = 5 
            if scene.camera_angle == "wide":
                clip = clip.resize(lambda t: 1 + 0.1 * t)
            elif scene.camera_angle == "close_up":
                clip = clip.set_position(lambda t: ('center', 50 - t * 10))
            elif scene.camera_angle == "birds_eye":
                # Slow zoom out
                clip = clip.resize(lambda t: 1.2 - 0.1 * t)
            
            return clip.set_duration(duration)
        except Exception as e:
            raise RuntimeError(f"Failed to apply camera movement: {str(e)}")
    
    @modal.method()
    async def create_video_clip(
        self,
        image_path: str,
        scene: ScenePanel
    ) -> ImageClip:
        """Create a video clip from an image with camera movements."""
        try:
            clip = ImageClip(image_path)
            return self.apply_camera_movement(clip, scene)
        except Exception as e:
            raise RuntimeError(f"Failed to create video clip: {str(e)}")

@app.function()
def image_to_video(
    image_sequence: List[AssetResult],
    scene_metadata: ScenePanel
) -> AssetResult:
    """Animates generated images into video clips with cinematic motion."""
    try:
        processor = VideoProcessor()
        
        # Create video clips from images with camera movements
        clips = []
        for image_asset in image_sequence:
            clip = processor.create_video_clip.remote(
                image_path=image_asset.storage_path,
                scene=scene_metadata
            )
            clips.append(clip)
        
        # Concatenate clips
        final_video = concatenate_videoclips(clips)
        output_path = f"{VIDEO_PATH}/video_{scene_metadata.panel_id}.mp4"
        
        # Write video file with optimized settings
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio=False,
            preset='medium',
            threads=4,
            bitrate='2000k'
        )
        
        return AssetResult(
            scene_id=scene_metadata.panel_id,
            asset_type=AssetType.VIDEO,
            storage_path=output_path,
            generation_metadata={
                "fps": "24",
                "codec": "libx264",
                "duration": str(final_video.duration),
                "bitrate": "2000k",
                "preset": "medium"
            }
        )
    except Exception as e:
        raise RuntimeError(f"Video generation failed: {str(e)}")
