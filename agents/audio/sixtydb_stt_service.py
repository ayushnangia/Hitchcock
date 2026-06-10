"""60db Speech-to-Text utility.

Hitchcock's default pipeline starts from a typed idea, so there is no
audio-input consumer in the current control plane. This module ships
the integration anyway, so future agents (or external CLIs) can
transcribe wav/mp3/m4a files into text without re-deriving the API
contract.

Typical use:

    from agents.audio.sixtydb_stt_service import SixtyDbSTTService
    text = SixtyDbSTTService().transcribe("path/to/idea.wav")

Reference: https://docs.60db.ai/api-reference/stt/speech-to-text
"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Optional

import requests


class SixtyDbSTTService:
    """One-shot REST transcription wrapper around 60db /stt."""

    def __init__(self) -> None:
        self.api_key = os.getenv("SIXTYDB_API_KEY")
        if not self.api_key:
            raise ValueError("SIXTYDB_API_KEY environment variable not set")
        self.base_url = os.getenv("SIXTYDB_API_BASE", "https://api.60db.ai").rstrip("/")

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        diarize: bool = False,
        keywords: Optional[str] = None,
    ) -> Optional[str]:
        """Upload `audio_path` to 60db /stt and return the transcript.

        Args:
            audio_path: path to a wav/mp3/m4a/ogg/flac/webm/mp4 file.
                        60db's per-file limit is 10 MB / 1 hour.
            language:   ISO 639-1 hint, or None for auto-detect.
            diarize:    enable speaker labels (adds 50–150 ms latency).
            keywords:   CSV vocab boost, optional `:weight` suffix per word.

        Returns:
            Full normalized transcript string, or None on failure.
        """
        path = Path(audio_path)
        if not path.is_file():
            print(f"60db STT: file not found: {audio_path}")
            return None

        content_type, _ = mimetypes.guess_type(path.name)
        content_type = content_type or "application/octet-stream"

        headers = {"Authorization": f"Bearer {self.api_key}"}
        data: dict[str, str] = {}
        # Auto-detect when language is unset; honor explicit override.
        lang = language or os.getenv("SIXTYDB_STT_LANGUAGE", "auto")
        if lang and lang.lower() != "auto":
            data["language"] = lang
        if diarize:
            data["diarize"] = "true"
        if keywords:
            data["keywords"] = keywords

        try:
            with path.open("rb") as f:
                files = {"file": (path.name, f, content_type)}
                response = requests.post(
                    f"{self.base_url}/stt",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=120,
                )
            response.raise_for_status()
            payload = response.json()
            return (payload.get("text") or "").strip() or None
        except requests.exceptions.RequestException as e:
            print(f"60db STT: error transcribing {audio_path}: {e}")
            return None
