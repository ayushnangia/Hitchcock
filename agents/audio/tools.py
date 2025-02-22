from typing import Dict, List
from agents.audio.storage import AudioStorage
from agents.audio.eleven_labs_service import ElevenLabsService
import os
from mutagen.mp3 import MP3
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import glob

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
    audio_service = ElevenLabsService()
    
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
            
            # Calculate duration for each image
            image_duration = audio_duration / len(image_files)
            
            # Create video clips for each image
            video_clips = []
            for img_path in image_files:
                clip = ImageClip(img_path).set_duration(image_duration)
                video_clips.append(clip)
            
            # Combine all clips
            final_clip = concatenate_videoclips(video_clips)
            
            # Add audio
            audio_clip = AudioFileClip(audio_file)
            final_clip = final_clip.set_audio(audio_clip)
            
            # Write output video
            output_path = os.path.join(video_dir, f"{scene_id}.mp4")
            final_clip.write_videofile(output_path, 
                                     fps=24, 
                                     codec='libx264',
                                     audio_codec='aac')
            
            # Clean up
            final_clip.close()
            audio_clip.close()
            for clip in video_clips:
                clip.close()
                
            processed_videos.append(output_path)
            print(f"Created video: {output_path}")
            
        except Exception as e:
            print(f"Error processing scene {scene_id}: {str(e)}")
            continue
    
    return f"Created {len(processed_videos)} videos in the output/videos directory"

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