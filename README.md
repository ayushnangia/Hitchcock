# Hitchcock - AI-Powered Movie Production Pipeline

Hitchcock is an innovative multi-agent system that automates the movie production pipeline from script to screen. Built with modern AI technologies, it orchestrates specialized agents to handle different aspects of movie production, from scriptwriting to audio synthesis.

## 🎯 Key Features

- **Automated Script Generation**: AI-powered script creation with deep research capabilities
- **Intelligent Story Boarding**: Automated scene breakdown and shot planning
- **Visual Element Planning**: Comprehensive planning of lighting, props, and atmosphere
- **Audio Synthesis**: Voice generation and audio management
- **Multi-Agent Architecture**: Specialized agents working together in a coordinated pipeline
- **Modern Tech Stack**: Built with Python 3.8+, using cutting-edge AI and media processing libraries

## 🏗 System Architecture

![Hitchcock Architecture](assets/arch_v1.png)

The system consists of the following specialized agents:

### 1. Script Writer Agent
- **Purpose**: Creates and analyzes movie scripts
- **Capabilities**:
  - Deep web research for historical/cultural context
  - Similar movie analysis for inspiration
  - Scene and dialogue generation
  - Script structure analysis
- **Tools**:
  - Web browsing and research tools
  - Text analysis and inspection
  - Scene generation and analysis
  - Research agent for deep context gathering

### 2. Story Boarding Agent
- **Purpose**: Converts scripts into detailed visual plans
- **Capabilities**:
  - Scene importance analysis
  - Shot sequence planning
  - Visual element specification
  - Camera angle and movement planning
- **Features**:
  - Automatic scene breakdown
  - Shot-by-shot planning
  - Lighting and atmosphere specification
  - Prop and special effect planning
  - Database integration for state management

### 3. Director of Photography (DOP) Agent
- **Purpose**: Handles visual implementation of story boards
- **Capabilities**:
  - Text-to-image generation
  - Scene composition
  - Visual continuity management
  - Lighting implementation
- **Features**:
  - Image generation services
  - Video sequence creation
  - Visual style consistency
  - Configuration management

### 4. Audio Agent
- **Purpose**: Manages audio synthesis and voice generation
- **Capabilities**:
  - Voice synthesis using Eleven Labs
  - Audio storage and retrieval
  - Voice consistency management
- **Features**:
  - Character voice generation
  - Audio file management
  - Integration with video pipeline

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- `uv` package manager

### Installation

1. Install uv:
```bash
pip install uv
```

2. Clone the repository:
```bash
git clone https://github.com/ayushnangia/Hitchcock
cd hitchcock
```

3. Set up the environment:
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

### Configuration
0. Fix Mahilo in venv
add in mahilo/agent.py

in process_queue_message and process_chat_message function add
```python
                try:
                    if function_name == "contact_human":
                        function_response = await function_to_call(**function_args, websockets=websockets)

                    elif function_name == "generate_shot_images":
                        function_response = await function_to_call(**function_args)
```



1. Configure environment variables:
```bash
cp .env.template .env
# Edit .env with your API keys and configurations
```
2. Always Remove old db and sessions
```bash
sh run_db_dele.sh
``` 

3. Start the control plane:
```bash
python control_plane.py
```

4. Start the script writer agent:
```bash
mahilo mahilo connect --agent-name StoryWriterAgent
``` 

5. Talk to the agent
```bash
mahilo mahilo chat --agent-name [StoryWriterAgent|StoryBoarderAgent|DOPAgent|AudioAgent]
```

## 📁 Project Structure

```
hitchcock/
├── control_plane.py      # Main orchestration system
├── requirements.txt      # Project dependencies
├── .env.template        # Environment variable template
├── agents/
│   ├── script_writer/   # Script Writer Agent
│   │   ├── tools.py     # Script writing tools
│   │   ├── prompt.py    # Agent prompts
│   │   ├── research_agent.py  # Research capabilities
│   │   └── scripts/     # Additional scripts
│   ├── story_boarder/   # Story Boarding Agent
│   │   ├── tools.py     # Story boarding tools
│   │   ├── prompt.py    # Agent prompts
│   │   ├── storage.py   # State management
│   │   ├── models.py    # Data models
│   │   └── db_client.py # Database operations
│   ├── dop/            # DOP Agent
│   │   ├── tools.py     # Visual tools
│   │   ├── prompt.py    # Agent prompts
│   │   ├── image_service.py  # Image generation
│   │   └── generate_story_video.py  # Video creation
│   └── audio/          # Audio Agent
│       ├── tools.py     # Audio processing tools
│       ├── prompt.py    # Agent prompts
│       ├── models.py    # Audio data models
│       └── eleven_labs_service.py  # Voice synthesis
├── assets/             # Project assets
├── downloads/          # Downloaded research materials
├── output/            # Generated content
└── sessions/          # Session management
```

## 🛠 Development

### Managing Dependencies

Add new dependencies:
```bash
uv pip install package_name
uv pip compile  # Update requirements.txt
```

Update all dependencies:
```bash
uv pip compile --upgrade
uv pip sync
```

Test with minimum versions:
```bash
uv pip compile --resolution=lowest
uv pip sync
```

### Running Individual Components

Run script writer:
```bash
python run_script_writer.py
```

### Database Management

Manage database:
```bash
./run_db_dele.sh
```

## 📝 License

MIT

---
*Note: This is an active development project. Features and capabilities may change as development progresses.*
