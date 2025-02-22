# Hitchcock: AI-Driven Video Generation Pipeline

Hitchcock is a sophisticated multi-agent movie maker that transforms storyboard descriptions into cinematic videos using state-of-the-art AI models.

## Architecture

### Core Components

1. **Storyboard Engine**
   - Processes structured scene descriptions
   - Manages character continuity and visual themes
   - Uses Pydantic for robust data validation

2. **Image Generation Service**
   - Leverages Stable Diffusion XL for high-quality image generation
   - Maintains visual consistency across frames
   - Handles character and environment rendering

3. **Video Processing Pipeline**
   - Converts image sequences to video
   - Implements cinematic camera movements
   - Manages temporal consistency

4. **Asset Management**
   - Stores and retrieves generated assets
   - Handles metadata and relationships
   - Integrates with VideoDB for efficient storage

### Tech Stack

- **Framework**: Modal (Serverless deployment)
- **Image Generation**: HuggingFace Diffusers
- **Video Processing**: MoviePy
- **Data Validation**: Pydantic v2
- **Asset Storage**: VideoDB

## Setup

```bash
# Clone the repository
git clone https://github.com/ayushnangia/Hitchcock.git
cd Hitchcock

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
├── hitchcock/
│   ├── core/
│   │   ├── models.py      # Pydantic models
│   │   └── config.py      # Configuration management
│   ├── services/
│   │   ├── image.py       # Image generation service
│   │   ├── video.py       # Video processing service
│   │   └── storage.py     # Asset management
│   └── utils/
│       ├── validators.py  # Custom validators
│       └── helpers.py     # Utility functions
├── tests/
├── requirements.txt
└── README.md
```

## License

MIT
