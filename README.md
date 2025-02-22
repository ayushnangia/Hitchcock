# Hitchcock - AI-Powered Movie Production Pipeline

Hitchcock is an innovative multi-agent system for automated movie production, leveraging AI to streamline the creative process from script to screen. This project, developed as part of the Eleven Labs hack, orchestrates multiple specialized AI agents to handle different aspects of movie production.

## System Architecture

![Hitchcock Architecture](assets/arch_v1.png)

The architecture diagram above illustrates the complete pipeline flow and agent interactions. The system uses `uv` for fast, reliable dependency management and virtual environment handling.

## Architecture Overview

The system follows a modular pipeline architecture with the following key components:

### 1. Script Writer (SW)
- **Input**: Theme & criteria (e.g., "horror with clowns set in Tripura")
- **Capabilities**:
  - Deep research integration for historical/cultural context
  - Similar movie analysis for inspiration
  - Theme-appropriate dialogue generation
  - Scene description and narrative structure
- **Tools**:
  - `research_historical_context`: Deep research on time periods and locations
  - `analyze_similar_movies`: Analysis of thematically similar films

### 2. Story Boarding (SB)
- **Input**: Script from SW
- **Features**:
  - Frame-by-frame script association
  - Camera angle specification
  - Lighting direction optimization
  - Position mapping and scene composition
- **Integration**: 
  - Uses VLM (Vision Language Model) like Claude for scene interpretation
  - Real-time scene visualization and validation

### 3. Character/Actor Generation (AC)
- **Capabilities**:
  - Custom actor generation with face consistency
  - Materialized actor tools
  - Talking style definition
  - Costume/clothing specification
- **Output**: Actor correlations for DOP integration

### 4. Director of Photography (DOP)
- **Input**: 
  - Story board panels
  - Actor correlations
- **Features**:
  - Text-to-image generation for each frame
  - Real-time feedback loop with Story Boarding
  - Scene composition and visual continuity
  - Advanced lighting and color correction

### 5. Cinematographer (C)
- **Responsibilities**:
  - High-performance image to video conversion
  - Video database management
  - Storage and retrieval systems
  - Frame stitching and sequence management
- **Features**:
  - High-performance frame processing
  - Consistent style transfer
  - Real-time frame interpolation

### 6. Editing & Post-Production
- **Capabilities**:
  - Video compilation
  - Smart transition management
  - Final output generation
  - Real-time preview rendering

## Technical Requirements

- Python 3.8+
- mahilo==0.5.0 (Agent management framework)
- Additional dependencies are managed via `uv`


## Known Challenges

1. **Consistency Management**:
   - Character face consistency across frames
   - Lighting and scene continuity
   - Style preservation throughout the pipeline
   - Cache management for large scenes

2. **Audio Integration**:
   - Voice synthesis and lip sync
   - Background score generation
   - Sound effect placement and synchronization
   - Audio-visual alignment

## Getting Started

1. Install uv:
```bash
pip install uv
```

2. Clone the repository:
```bash
git clone https://github.com/yourusername/hitchcock.git
cd hitchcock
```

3. Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Unix
# or
.venv\Scripts\activate  # On Windows
```

4. Install dependencies:
```bash
uv pip sync requirements.txt
```

5. Run the control plane:
```bash
python control_plane.py
```

## Project Structure

```
hitchcock/
├── docs/
│   └── arch_v1.png      # Architecture diagram
├── control_plane.py      # Main orchestration system
├── requirements.txt      # Project dependencies (managed by uv)
├── agents/
│   ├── script_writer/   # Script generation agent
│   │   ├── prompt.py    # Agent prompts and instructions
│   │   └── tools.py     # Script writing tools
│   └── dop/            # Director of Photography agent
│       ├── prompt.py    # DOP prompts and instructions
│       └── tools.py     # Photography and visual tools
```

## Development Workflow

1. Adding new dependencies:
```bash
uv pip install package_name
uv pip compile  # Update requirements.txt
```

2. Updating dependencies:
```bash
uv pip compile --upgrade
uv pip sync
```

3. Installing with lowest compatible versions (for testing):
```bash
uv pip compile --resolution=lowest
uv pip sync
```

---
*Note: This is an active development project. Features and capabilities may change as development progresses.*
