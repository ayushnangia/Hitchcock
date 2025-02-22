import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from smolagents import Tool, LiteLLMModel
from .research_agent import ScriptWriterResearchAgent
from .scripts.text_web_browser import (
    SimpleTextBrowser,
    SearchInformationTool,
    VisitTool,
    PageUpTool,
    PageDownTool,
    FinderTool,
    FindNextTool,
    ArchiveSearchTool,
)
from .scripts.text_inspector_tool import TextInspectorTool

load_dotenv(override=True)


class ScriptAnalysisTool(Tool):
    name = "analyze_script_structure"
    description = "Analyze script structure and provide feedback"
    inputs = {
        "script_text": {
            "type": "string",
            "description": "Script text to analyze"
        }
    }
    output_type = "string"

    def __init__(self, model: LiteLLMModel):
        super().__init__()
        self.model = model

    def forward(self, script_text: str) -> str:
        response = self.model.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional script analyst. Analyze this script's structure and provide detailed feedback."},
                {"role": "user", "content": script_text}
            ]
        )
        return response.choices[0].message.content

class SceneGeneratorTool(Tool):
    name = "generate_scene"
    description = "Generate a new scene based on parameters"
    inputs = {
        "scene_description": {"type": "string", "description": "Description of the scene"},
        "characters": {"type": "array", "items": {"type": "string"}, "description": "Characters in the scene"},
        "tone": {"type": "string", "description": "Tone of the scene"},
        "setting": {"type": "string", "description": "Setting of the scene"}
    }
    output_type = "string"

    def __init__(self, model: LiteLLMModel):
        super().__init__()
        self.model = model

    def forward(self, scene_description: str, characters: List[str], tone: str, setting: str) -> str:
        prompt = f"""Generate a movie script scene with:
        Description: {scene_description}
        Characters: {', '.join(characters)}
        Tone: {tone}
        Setting: {setting}
        
        Follow standard screenplay format."""
        
        response = self.model.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a professional screenwriter. Write a scene following standard screenplay format."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

class ScriptResearchTools:
    """Collection of research tools for script writing"""
    
    def __init__(self, model: LiteLLMModel):
        self.model = model  # Store model reference for use in methods
        
        # Configure browser
        self.browser = SimpleTextBrowser(
            viewport_size=1024 * 5,
            downloads_folder="downloads",
            request_kwargs={
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                "timeout": 300,
            },
            serpapi_key=os.getenv("SERPAPI_API_KEY")
        )
        
        # Initialize web tools
        self.web_tools = [
            SearchInformationTool(self.browser),
            VisitTool(self.browser),
            PageUpTool(self.browser),
            PageDownTool(self.browser),
            FinderTool(self.browser),
            FindNextTool(self.browser),
            ArchiveSearchTool(self.browser),
            TextInspectorTool(model, text_limit=100000)
        ]
        
        # Initialize script-specific tools
        self.script_tools = [
            ScriptAnalysisTool(model),
            SceneGeneratorTool(model)
        ]

def get_script_with_research(script_prompt: str) -> str:
    """
    Get a script with research using the ScriptWriterResearchAgent.
    This is a tool that can be used by the story writer Mahilo agent to generate scripts.
    
    Args:
        script_prompt (str): The prompt describing what kind of script to write
        
    Returns:
        str: The generated script text
    """
    # Initialize the agent with default settings
    agent = ScriptWriterResearchAgent(
        model_id="o1",  # Default model
        max_steps=20,   # Default max steps
        verbosity_level=2  # Default verbosity
    )
    
    # Generate the script using the agent
    script = agent.write_script(script_prompt)
    
    return script

# Add the script generation tool to the list of available tools
tools = [
    {
        "tool": {
            "type": "function",
            "function": {
                "name": "get_script_with_research",
                "description": "Generate a movie script with research capabilities",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "script_prompt": {
                            "type": "string",
                            "description": "Description of the script to generate (e.g., 'Write a thriller set in 1920s Chicago')"
                        }
                    },
                    "required": ["script_prompt"]
                }
            }
        },
        "function": get_script_with_research,
    }
]

