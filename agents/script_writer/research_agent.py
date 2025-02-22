import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from huggingface_hub import login
from smolagents import CodeAgent, LiteLLMModel, ToolCallingAgent
import litellm

from .tools import ScriptResearchTools
from .prompt import story_writer_prompt

# Load environment variables and login to Hugging Face
load_dotenv(override=True)
if os.getenv("HF_TOKEN"):
    login(os.getenv("HF_TOKEN"))

# Configure litellm to drop unsupported parameters
litellm.drop_params = True

AUTHORIZED_IMPORTS = [
    "requests",
    "os",
    "pandas",
    "numpy",
    "json",
    "bs4",
    "xml",
    "io",
    "datetime",
    "csv"
]

class ScriptWriterResearchAgent:
    """Agent for writing movie scripts with integrated research capabilities"""
    
    def __init__(
        self,
        model_id: str = "o1",
        max_steps: int = 20,
        verbosity_level: int = 2,
        planning_interval: int = 4,
        max_tokens: int = 4096
    ):
        # Initialize the LLM model
        self.model = LiteLLMModel(
            model_id,
            custom_role_conversions={"tool-call": "assistant", "tool-response": "user"},
            max_completion_tokens=max_tokens,
            temperature=0.7,
            top_p=0.95,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        
        # Initialize research tools
        self.research_tools = ScriptResearchTools(self.model)
        
        # Initialize the research agent
        self.research_agent = ToolCallingAgent(
            model=self.model,
            tools=self.research_tools.web_tools,
            max_steps=max_steps,
            verbosity_level=verbosity_level,
            planning_interval=planning_interval,
            name="research_agent",
            description="""A team member that will search the internet to research context and information for the script.
            Ask for any historical, cultural, or thematic research needed.
            Provide as much context as possible, especially for specific time periods or locations.""",
            provide_run_summary=True
        )
        
        # Add web browsing capabilities
        self.research_agent.prompt_templates["managed_agent"]["task"] += """
        You can navigate to .txt online files.
        If a non-html page is in another format, especially .pdf or a Youtube video, use tool 'inspect_file_as_text' to inspect it.
        Additionally, if after some searching you find out that you need more information, you can use `final_answer` with your request for clarification.
        """
        
        # Initialize the manager agent
        self.manager = CodeAgent(
            model=self.model,
            tools=self.research_tools.script_tools,
            max_steps=max_steps,
            verbosity_level=verbosity_level,
            additional_authorized_imports=AUTHORIZED_IMPORTS,
            planning_interval=planning_interval,
            managed_agents=[self.research_agent],
            name="script_writer",
            description=story_writer_prompt
        )
    
    def research_context(
        self,
        time_period: Optional[str] = None,
        location: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> str:
        """Research historical and cultural context"""
        query = f"Research historical and cultural context for {time_period if time_period else ''} {location if location else ''}"
        if additional_context:
            query += f" {additional_context}"
        return self.research_agent.run(query)
    
    def analyze_theme(self, theme: str) -> str:
        """Analyze similar movies with the given theme"""
        query = f"Research and analyze movies with the theme: {theme}"
        return self.research_agent.run(query)
    
    def write_script(self, prompt: str) -> str:
        """Write a script based on the given prompt, using research tools as needed"""
        return self.manager.run(prompt)
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools"""
        return self.research_tools.script_tools + self.research_tools.web_tools 