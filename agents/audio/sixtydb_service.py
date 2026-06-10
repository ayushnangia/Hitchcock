import base64
import os
from pathlib import Path
from typing import Optional

import requests


class SixtyDbService:
    """Service for interacting with the 60db TTS API.

    Drop-in peer of ElevenLabsService: same `generate_audio(text, scene_id)`
    signature, same `output/audio/{scene_id}.mp3` on-disk contract — so the
    audio agent's downstream ffmpeg pipeline (which globs SCENE_ID.mp3 +
    images/SCENE_ID_*.jpg) doesn't care which provider produced the file.

    Reference: https://docs.60db.ai/api-reference/tts/text-to-speech
    """

    DEFAULT_VOICE_ID = "fbb75ed2-975a-40c7-9e06-38e30524a9a1"  # docs example UUID

    def __init__(self):
        self.api_key = os.getenv("SIXTYDB_API_KEY")
        if not self.api_key:
            raise ValueError("SIXTYDB_API_KEY environment variable not set")
        self.base_url = os.getenv("SIXTYDB_API_BASE", "https://api.60db.ai").rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Same on-disk layout as ElevenLabsService so the rest of the
        # pipeline (tools.py:create_videos_from_audio_and_images) finds
        # the files without any glob changes.
        self.output_dir = Path("output/audio")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_audio(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,  # noqa: ARG002 — ignored, ElevenLabs-compat
        scene_id: Optional[str] = None,
    ) -> Optional[str]:
        """Synthesize `text` via 60db and write the mp3 to disk.

        Args:
            text:     Script text to vocalize. 60db caps individual requests
                      at 5000 chars; longer scenes should be split upstream.
            voice_id: Override the SIXTYDB_TTS_VOICE_ID env default.
            model_id: Accepted for ElevenLabs-signature compatibility; 60db
                      does not expose a model selector on /tts-synthesize,
                      so this argument is ignored.
            scene_id: Used as the output filename. Required — without it
                      the downstream ffmpeg glob can't match images.

        Returns:
            Path to the written mp3, or None if the API call failed.
        """
        if not scene_id:
            print("60db: scene_id required for filename")
            return None
        if len(text) > 5000:
            # Fail loudly rather than silently truncating — the audio
            # agent should split into chunks if scenes exceed the limit.
            print(f"60db: text too long for scene {scene_id} ({len(text)} > 5000 chars)")
            return None

        url = f"{self.base_url}/tts-synthesize"
        payload = {
            "text": text,
            "voice_id": voice_id or os.getenv("SIXTYDB_TTS_VOICE_ID", self.DEFAULT_VOICE_ID),
            "enhance": True,
            "speed": 1,
            "stability": 50,
            "similarity": 75,
            "output_format": "mp3",
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            audio_b64 = data.get("audio_base64")
            if not data.get("success") or not audio_b64:
                print(f"60db: empty audio for scene {scene_id} — {data.get('message')}")
                return None
            output_path = self.output_dir / f"{scene_id}.mp3"
            output_path.write_bytes(base64.b64decode(audio_b64))
            return str(output_path)
        except requests.exceptions.RequestException as e:
            print(f"60db: error generating audio for scene {scene_id}: {e}")
            return None
