from enum import Enum
from typing import List, Optional, Dict
from pydantic import Field
from .base import HitchcockBaseModel

class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"

class ProcessingStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AssetResult(HitchcockBaseModel):
    scene_id: str
    asset_type: AssetType
    storage_path: str
    generation_metadata: Dict[str, str] = Field(
        default={
            "model_version": "2.1",
            "inference_steps": "50"
        }
    )

class ProcessingResponse(HitchcockBaseModel):
    request_id: str
    status: ProcessingStatus
    assets: List[AssetResult]
    error_log: Optional[List[str]] = None
