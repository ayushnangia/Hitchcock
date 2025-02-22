import asyncio
import fal_client
import aiohttp
from typing import List, Dict, Optional
from agents.dop.models.scene import StoryboardRequest, ScenePanel, CameraAngle, CharacterDescription
from agents.dop.models.assets import AssetResult, AssetType, ProcessingResponse
import os
import json
from datetime import datetime
import base64
from moviepy.editor import VideoFileClip, concatenate_videoclips, clips_array
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from functools import partial

class VideoService:
    def __init__(self, output_dir: str = "output", max_workers: int = None):
        self.output_dir = output_dir
        self.video_dir = os.path.join(output_dir, "videos")
        self.metadata_dir = os.path.join(output_dir, "metadata")
        self.max_workers = max_workers or (os.cpu_count() or 1) * 2  # Default to 2x CPU cores
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

    async def upload_image_to_fal(self, image_path: str) -> str:
        """Upload a local image to FAL and get a public URL."""
        try:
            # Read the image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Convert to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Upload using the file upload API
            url = fal_client.upload_file(image_path)
            print(f"\n📤 Image uploaded successfully: {os.path.basename(image_path)}")
            return url
            
        except Exception as e:
            print(f"\n❌ Failed to upload image {image_path}: {str(e)}")
            raise

    async def generate_character_video(
        self,
        character: CharacterDescription,
        scene: ScenePanel,
        image_path: str,
        session_id: str,
        index: int
    ) -> Optional[str]:
        """Generate a video clip for a character using the FAL video API."""
        try:
            # First, upload the image to get a public URL
            print(f"\n📤 Uploading reference image for {character.name}...")
            public_image_url = await self.upload_image_to_fal(image_path)
            
            # Create scene-specific prompt for the character
            prompt = (
                f"{character.name} in a steampunk setting. "
                f"The character {scene.description}. "
                f"Their demeanor shows {character.demeanor['posture']}, "
                f"with {character.demeanor['movement']} movements. "
                "The environment is filled with brass and copper machinery, "
                "steam vents, and mechanical wonders."
            )

            print(f"\n🎬 Generating video for Character {index}: {character.name}")
            print("\n📝 Generated Prompt:")
            print(prompt)

            def on_queue_update(update):
                if isinstance(update, fal_client.InProgress):
                    for log in update.logs:
                        print(f"📋 {log['message']}")

            # Submit video generation request using subscribe pattern
            result = fal_client.subscribe(
                "fal-ai/minimax/video-01-subject-reference",
                arguments={
                    "prompt": prompt,
                    "subject_reference_image_url": public_image_url,
                    "prompt_optimizer": True
                },
                with_logs=True,
                on_queue_update=on_queue_update
            )

            if result and result.get("video"):
                video_url = result["video"]["url"]
                print(f"\n🎥 Video URL for {character.name}: {video_url}")
                
                # Download the video
                async with aiohttp.ClientSession() as session:
                    async with session.get(video_url) as resp:
                        if resp.status == 200:
                            filename = f"character_{index}_{character.name.lower()}_{session_id}.mp4"
                            video_path = os.path.join(self.video_dir, filename)
                            
                            with open(video_path, 'wb') as f:
                                f.write(await resp.read())
                            print(f"\n💾 Video saved as: {video_path}")
                            return video_path
            
            raise Exception("No video in the result")

        except Exception as e:
            print(f"\n❌ An error occurred while generating video for {character.name}: {str(e)}")
            return None

    async def preview_video(self, video_path: str, fps: int = 24) -> None:
        """Preview a video clip using MoviePy."""
        try:
            if not os.path.exists(video_path):
                print(f"❌ Video file not found: {video_path}")
                return
                
            clip = VideoFileClip(video_path)
            print(f"\n🎬 Previewing video: {os.path.basename(video_path)}")
            print(f"Duration: {clip.duration:.2f} seconds")
            print(f"Size: {clip.size}")
            print(f"FPS: {clip.fps}")
            
            # Preview the clip
            clip.preview(fps=fps)
            clip.close()
            
        except Exception as e:
            print(f"❌ Failed to preview video: {str(e)}")

    def _process_video_clip(self, video_path: str, target_duration: float = 5.0, target_size: tuple = None) -> Optional[VideoFileClip]:
        """Process a video clip in a separate thread."""
        try:
            if not os.path.exists(video_path):
                print(f"⚠️ Video file not found: {video_path}")
                return None

            clip = VideoFileClip(video_path)
            
            # Resize if needed
            if target_size and clip.size != target_size:
                print(f"⚠️ Resizing clip to {target_size}")
                clip = clip.resize(target_size)
            
            # Normalize duration
            if clip.duration > target_duration:
                print(f"⚠️ Adjusting clip duration from {clip.duration:.2f}s to {target_duration:.2f}s")
                clip = clip.subclip(0, target_duration)
            
            return clip
        except Exception as e:
            print(f"⚠️ Failed to process clip {video_path}: {str(e)}")
            return None

    async def stitch_videos(self, video_paths: List[str], scene: ScenePanel, session_id: str) -> Optional[str]:
        """Combine multiple character videos into a single scene using thread pool."""
        clips = []
        temp_files = []
        
        try:
            print(f"\n🎬 Starting video stitching process with {self.max_workers} workers...")
            
            # Process clips in parallel using thread pool
            first_clip = None
            target_size = None
            
            # First, process one clip to get target dimensions
            for path in video_paths:
                first_clip = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool, 
                    self._process_video_clip, 
                    path, 
                    5.0, 
                    None
                )
                if first_clip:
                    target_size = first_clip.size
                    clips.append(first_clip)
                    break
            
            if not first_clip:
                raise Exception("Failed to process any clips")
            
            # Process remaining clips in parallel
            futures = []
            for path in video_paths[1:]:
                future = asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    self._process_video_clip,
                    path,
                    5.0,
                    target_size
                )
                futures.append(future)
            
            # Wait for all processing to complete
            processed_clips = await asyncio.gather(*futures)
            clips.extend([clip for clip in processed_clips if clip is not None])
            
            if not clips:
                raise Exception("No valid video clips to stitch")
            
            print(f"\n📊 Stitching {len(clips)} clips...")
            
            # Create final video
            if len(clips) == 1:
                final_video = clips[0]
            else:
                # Normalize durations to shortest clip
                min_duration = min(c.duration for c in clips)
                
                # Process clip normalization in parallel
                futures = []
                for clip in clips:
                    future = asyncio.get_event_loop().run_in_executor(
                        self.thread_pool,
                        lambda c: c.subclip(0, min_duration),
                        clip
                    )
                    futures.append(future)
                
                normalized_clips = await asyncio.gather(*futures)
                
                if scene.camera_angle == CameraAngle.WIDE:
                    # For wide shots, concatenate horizontally
                    final_video = concatenate_videoclips(normalized_clips, method="compose")
                else:
                    # For other angles, create a grid layout
                    clip_rows = [normalized_clips[i:i+2] for i in range(0, len(normalized_clips), 2)]
                    final_video = clips_array(clip_rows)
            
            # Export final video
            output_filename = f"scene_{scene.panel_id}_{session_id}.mp4"
            output_path = os.path.join(self.video_dir, output_filename)
            
            print("\n💾 Writing final video...")
            
            # Write video file in a thread
            await asyncio.get_event_loop().run_in_executor(
                self.thread_pool,
                partial(
                    final_video.write_videofile,
                    output_path,
                    fps=24,
                    codec='libx264',
                    audio=False,
                    preset='medium',
                    threads=self.max_workers,  # Use all available workers for encoding
                    bitrate='2000k',
                    logger=None
                )
            )
            
            print(f"✨ Final video saved: {output_path}")
            
            # Preview the final result
            await self.preview_video(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"\n❌ Failed to stitch videos: {str(e)}")
            return None
            
        finally:
            # Clean up resources in parallel
            if clips:
                cleanup_futures = []
                for clip in clips:
                    future = asyncio.get_event_loop().run_in_executor(
                        self.thread_pool,
                        lambda c: c.close() if c else None,
                        clip
                    )
                    cleanup_futures.append(future)
                await asyncio.gather(*cleanup_futures)
            
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.remove(temp_file)
                except:
                    pass

    async def process_scene(
        self,
        scene: ScenePanel,
        characters: Dict[str, CharacterDescription],
        character_images: Dict[str, str],
        session_id: str
    ) -> Optional[AssetResult]:
        """Process a scene with multiple characters and generate a final video concurrently."""
        try:
            print(f"\n🎭 Starting concurrent video generation for {len(characters)} characters...")
            
            # Create tasks for all character video generations
            async def process_character(char_id: str, character: CharacterDescription, index: int) -> Optional[str]:
                if char_id not in character_images:
                    print(f"⚠️ No image found for character {char_id}")
                    return None
                    
                return await self.generate_character_video(
                    character=character,
                    scene=scene,
                    image_path=character_images[char_id],
                    session_id=session_id,
                    index=index
                )

            # Generate all videos concurrently
            tasks = [
                process_character(char_id, character, idx + 1)
                for idx, (char_id, character) in enumerate(characters.items())
            ]
            
            # Wait for all video generations to complete
            video_paths = await asyncio.gather(*tasks)
            
            # Filter out None values from failed generations
            valid_video_paths = [path for path in video_paths if path is not None]
            
            if not valid_video_paths:
                raise Exception("No valid videos were generated")
            
            print(f"\n✅ Generated {len(valid_video_paths)} videos successfully")
            
            # Stitch the videos together
            final_video_path = await self.stitch_videos(valid_video_paths, scene, session_id)
            
            if final_video_path:
                return AssetResult(
                    scene_id=scene.panel_id,
                    asset_type=AssetType.VIDEO,
                    storage_path=final_video_path,
                    generation_metadata={
                        "fps": "24",
                        "codec": "libx264",
                        "characters": list(characters.keys()),
                        "scene_description": scene.description,
                        "successful_generations": len(valid_video_paths),
                        "total_characters": len(characters)
                    }
                )
            
            raise Exception("Failed to generate final video")
            
        except Exception as e:
            print(f"\n❌ Scene processing failed: {str(e)}")
            return None
