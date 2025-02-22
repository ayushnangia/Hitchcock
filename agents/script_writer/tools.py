from agents.script_writer.research_agent import ScriptWriterResearchAgent


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