from typing import Dict, List
from agents.audio.storage import AudioStorage
from agents.audio.eleven_labs_service import ElevenLabsService
from agents.audio.sixtydb_service import SixtyDbService
import os
from mutagen.mp3 import MP3
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import glob
import subprocess


def _get_audio_service():
    """Pick the TTS backend based on AUDIO_PROVIDER env var.

    Both services expose the same `generate_audio(text, scene_id)`
    interface and write `output/audio/{scene_id}.mp3`, so the rest of
    this file (ffmpeg pipeline, file globs) is provider-agnostic.

    Defaults to ElevenLabs to keep existing setups working.
    """
    provider = os.getenv("AUDIO_PROVIDER", "elevenlabs").strip().lower()
    if provider in ("60db", "sixtydb"):
        return SixtyDbService()
    return ElevenLabsService()

def process_scripts_for_audio() -> str:
    """
    Load all shot images from the database, extract scene IDs,
    and fetch corresponding script data for audio processing.
    Uses Eleven Labs to generate audio for each script.
    
    Returns:
        A string message indicating where the audio files were created.
    """
    # Initialize storage and audio service clients
    storage = AudioStorage()
    audio_service = _get_audio_service()
    
    # Get all shot specs from storage
    shot_specs = storage.load_shot_image_specs()
    
    # Extract unique scene IDs
    scene_ids = list(set(spec.scene_id for spec in shot_specs))
    
    # Track generated audio files
    generated_files = []
    
    # Fetch script data for each scene
    for scene_id in scene_ids:
        script_data = storage.get_script_by_id(scene_id)
        if script_data:
            print(f"\nProcessing Scene: {script_data['title']}")
            print(f"Characters: {', '.join(script_data['characters'])}")
            print(f"Description: {script_data['description']}")
            
            # Generate audio for the script text
            audio_path = audio_service.generate_audio(text=script_data['script_text'], scene_id=scene_id)
            if audio_path:
                generated_files.append(audio_path)
                print(f"Generated audio file: {audio_path}")
            else:
                print(f"Failed to generate audio for scene: {script_data['title']}")
            
            print("-" * 80)

    create_videos_from_audio_and_images()
    
    return f"Generated {len(generated_files)} audio files in the output/audio directory"

def create_videos_from_audio_and_images() -> str:
    """
    Create videos by combining audio files with corresponding images.
    For each audio file (SCENE_ID.mp3), finds all images with matching SCENE_ID
    and creates a video where the images are shown for equal durations.
    After processing, re-encode each video to ensure container consistency
    and concatenate them into a final video.
    
    Returns:
        A string message indicating where the videos were created.
    """
    # Setup output directories  
    output_dir = "output"
    audio_dir = os.path.join(output_dir, "audio")
    image_dir = os.path.join(output_dir, "images")
    video_dir = os.path.join(output_dir, "videos")
    os.makedirs(video_dir, exist_ok=True)
    
    # Track processed videos
    processed_videos = []
    
    # Process each audio file
    for audio_file in glob.glob(os.path.join(audio_dir, "*.mp3")):
        try:
            # Extract scene ID from audio filename
            scene_id = os.path.basename(audio_file).replace(".mp3", "")
            
            # Find corresponding images
            image_pattern = os.path.join(image_dir, f"{scene_id}_*.jpg")
            image_files = sorted(glob.glob(image_pattern))
            
            if not image_files:
                print(f"No images found for scene {scene_id}")
                continue
                
            # Get audio duration
            audio = MP3(audio_file)
            audio_duration = audio.info.length
            
            # Calculate duration for each image (ensure at least one frame duration at 24fps)
            frame_duration = 1/24  # duration for one frame at 24fps
            image_duration = max(audio_duration / len(image_files), frame_duration)
            
            # Build FFmpeg command for creating the scene video
            output_path = os.path.join(video_dir, f"{scene_id}.mp4")
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',
                '-framerate', f'1/{image_duration}',  # Input framerate from calculated duration
                '-pattern_type', 'glob',
                '-i', image_pattern,
                '-i', audio_file,
                '-fflags', '+genpts',  # Regenerate presentation timestamps
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,'
                       'pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
                '-preset', 'ultrafast',
                '-tune', 'stillimage',
                '-crf', '23',
                '-c:a', 'aac',
                '-shortest',
                output_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            processed_videos.append(output_path)
            print(f"Created video: {output_path}")
            
        except Exception as e:
            print(f"Error processing scene {scene_id}: {str(e)}")
            continue

    # If any videos were created, standardize and then concatenate them
    if processed_videos:
        # Sort videos by scene name
        processed_videos.sort()

        # Re-encode each video to enforce consistent container settings
        standardized_videos = []
        for video in processed_videos:
            standardized_video = os.path.join(video_dir, f"std_{os.path.basename(video)}")
            ffmpeg_reencode_cmd = [
                'ffmpeg',
                '-y',
                '-i', video,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-r', '24',               # Force frame rate to 24fps
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                standardized_video
            ]
            subprocess.run(ffmpeg_reencode_cmd, check=True, capture_output=True)
            standardized_videos.append(standardized_video)
            print(f"Standardized video: {standardized_video}")

        # Create a text file listing all standardized videos to concatenate
        concat_file = os.path.join(video_dir, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for video in standardized_videos:
                abs_path = os.path.abspath(video)
                f.write(f"file '{abs_path}'\n")
        
        # Build FFmpeg command for concatenation using stream copy
        final_output = os.path.join(video_dir, "final.mp4")
        concat_cmd = [
            'ffmpeg',
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',  # Using stream copy to avoid further re-encoding
            final_output
        ]
        
        try:
            subprocess.run(concat_cmd, check=True, capture_output=True)
            print(f"\nCreated final video: {final_output}")
            # Clean up the concat list file
            os.remove(concat_file)
        except Exception as e:
            print(f"Error creating final video: {str(e)}")
    
    return f"Created {len(processed_videos)} videos in the output/videos directory and combined them into final.mp4"

# Add the script processing tool to the list of available tools
tools = [
    {
        "tool": {
            "type": "function",
            "function": {
                "name": "process_scripts_for_audio",
                "description": "Load shot images, extract scene IDs, and generate audio for scripts using Eleven Labs",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        "function": process_scripts_for_audio,
    }
]