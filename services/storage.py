from typing import List
import modal
from datetime import datetime
from models import (
    AssetResult,
    ProcessingResponse,
    ProcessingStatus
)

# Initialize Modal app
app = modal.App("hitchcock-storage")

# Define storage paths
STORAGE_PATH = "/assets"

# Create persistent volume for assets
volume = modal.Volume.from_name("hitchcock-assets", create_if_missing=True)

# Create base image with all dependencies
image = (modal.Image.debian_slim()
    .pip_install(
        "python-magic==0.4.27",
        "boto3==1.34.0",
        "aiofiles==23.2.1",
        "fsspec==2024.2.0"
    )
    .add_local_python_source("config", "models")
)

@app.cls(
    image=image,
    volumes={STORAGE_PATH: volume},
    cpu=2,
    memory=4096
)
class AssetManager:
    def __init__(self):
        self.base_path = STORAGE_PATH
        
    def __enter__(self):
        """Initialize resources when the container starts."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup when the container exits."""
        pass
    
    def store_asset(self, asset: AssetResult) -> str:
        """Store an asset in the persistent storage."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_path = f"{self.base_path}/{asset.scene_id}_{timestamp}.{asset.asset_type}"
            
            # Copy from temporary location to persistent storage
            with open(asset.storage_path, 'rb') as src, open(new_path, 'wb') as dst:
                dst.write(src.read())
            
            return new_path
        except Exception as e:
            raise RuntimeError(f"Failed to store asset {asset.scene_id}: {str(e)}")
    
    @modal.method()
    def process_assets(
        self,
        assets: List[AssetResult],
        request_id: str
    ) -> ProcessingResponse:
        """Process and store a batch of assets."""
        stored_assets = []
        error_log = []
        
        try:
            for asset in assets:
                try:
                    new_path = self.store_asset(asset)
                    asset.storage_path = new_path
                    stored_assets.append(asset)
                except Exception as e:
                    error_log.append(f"Failed to store {asset.scene_id}: {str(e)}")
            
            status = (
                ProcessingStatus.COMPLETED
                if not error_log
                else ProcessingStatus.PARTIAL_FAILURE if stored_assets else ProcessingStatus.FAILED
            )
            
            return ProcessingResponse(
                request_id=request_id,
                status=status,
                assets=stored_assets,
                error_log=error_log if error_log else None,
                temporal_consistency_check=True if stored_assets else False,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return ProcessingResponse(
                request_id=request_id,
                status=ProcessingStatus.FAILED,
                assets=[],
                error_log=[f"Processing failed: {str(e)}"],
                temporal_consistency_check=False,
                timestamp=datetime.now().isoformat()
            )

@app.function()
def stitch_and_store(
    video_assets: List[AssetResult],
    output_spec: dict
) -> ProcessingResponse:
    """Store processed video assets and return final processing report."""
    try:
        manager = AssetManager()
        request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return manager.process_assets.remote(
            assets=video_assets,
            request_id=request_id
        )
    except Exception as e:
        return ProcessingResponse(
            request_id=f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status=ProcessingStatus.FAILED,
            assets=[],
            error_log=[f"Failed to stitch and store: {str(e)}"],
            temporal_consistency_check=False,
            timestamp=datetime.now().isoformat()
        )
