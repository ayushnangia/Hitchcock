from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the absolute paths
BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent
OUTPUT_DIR = PARENT_DIR / "output"
STATIC_DIR = BASE_DIR / "static"

logger.info(f"Base directory: {BASE_DIR}")
logger.info(f"Parent directory: {PARENT_DIR}")
logger.info(f"Output directory: {OUTPUT_DIR}")
logger.info(f"Static directory: {STATIC_DIR}")

# Create static directory if it doesn't exist
STATIC_DIR.mkdir(exist_ok=True)

# Mount static directories
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    try:
        html_file = STATIC_DIR / "index.html"
        if not html_file.exists():
            logger.error(f"HTML file not found at {html_file}")
            raise HTTPException(status_code=404, detail="HTML file not found")
            
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def list_files():
    """List all media files in the output directory"""
    try:
        logger.info("Attempting to list files")
        logger.info(f"Checking images directory: {OUTPUT_DIR / 'images'}")
        logger.info(f"Checking videos directory: {OUTPUT_DIR / 'videos'}")  # Updated to 'videos'
        
        def safe_list_dir(path: Path) -> list:
            try:
                if not path.exists():
                    logger.warning(f"Directory does not exist: {path}")
                    return []
                return [f for f in os.listdir(path) if not f.startswith('.')]
            except Exception as e:
                logger.error(f"Error listing directory {path}: {str(e)}")
                return []

        # Updated path for videos directory
        images = safe_list_dir(OUTPUT_DIR / "images")
        videos = safe_list_dir(OUTPUT_DIR / "videos")
        audio = safe_list_dir(OUTPUT_DIR / "audio")  # Add audio files
        metadata = safe_list_dir(OUTPUT_DIR / "metadata")

        logger.info(f"Found images: {images}")
        logger.info(f"Found videos: {videos}")
        logger.info(f"Found metadata: {metadata}")

        return {
            "images": sorted(images),
            "videos": sorted(videos),
            "audio": sorted(audio),
            "metadata": sorted(metadata)
        }
    except Exception as e:
        logger.error(f"Error in list_files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
