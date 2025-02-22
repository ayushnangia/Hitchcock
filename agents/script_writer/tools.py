import os
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
    # make file if not exists
    if not os.path.exists("data/script_writer"):
        os.makedirs("data/script_writer")

    # write it to a file
    with open("data/script_writer/script.txt", "w") as f:
        f.write(script)
    
    # Extract and save characters
    extract_and_save_characters(script)
    
    return "I have saved the script to data/script_writer/script.txt and extracted character information to the database"

def extract_and_save_characters(script_text: str) -> str:
    """
    Extract character information from the script and save it to the storyboard database.
    This function should be called after the script is generated.
    
    Args:
        script_text (str): The full text of the generated script
        
    Returns:
        str: A message indicating success and summary of characters saved
    """
    from agents.story_boarder.db_client import StoryboardDBClient
    import instructor
    from openai import OpenAI
    from pydantic import BaseModel
    from typing import List
    
    class Character(BaseModel):
        """Character information extracted from the script"""
        name: str
        description: str
        role: str  # main, supporting, etc.
        traits: str  # comma-separated list of traits
    
    # Initialize OpenAI client with instructor
    client = instructor.patch(OpenAI())
    
    # Create prompt for character extraction
    prompt = f"""
    Analyze this script and extract detailed information about all characters.
    For each character, identify:
    1. Their full name as it appears in the script
    2. A comprehensive description of their character
    3. Their role in the story (main or supporting)
    4. Their key personality traits and characteristics
    
    Focus on both explicitly stated and implied character traits.
    Include any character development or changes throughout the story.
    
    Script to analyze:
    {script_text}
    """
    
    try:
        # Use OpenAI to extract character information
        characters = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=List[Character],
            messages=[
                {"role": "system", "content": "You are a professional script analyst specializing in character analysis and development."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Convert to format expected by database
        db_characters = [
            {
                "name": char.name,
                "description": char.description,
                "role": char.role,
                "traits": char.traits
            }
            for char in characters
        ]
        
        # Save to database
        db = StoryboardDBClient()
        db.save_script_characters(db_characters)
        
        return f"Successfully extracted and saved {len(db_characters)} characters to the database"
        
    except Exception as e:
        print(f"Error extracting characters: {e}")
        # Create a minimal fallback character list
        fallback_chars = [{
            "name": "Unknown Character",
            "description": "Error occurred during character extraction",
            "role": "unknown",
            "traits": "unknown"
        }]
        db = StoryboardDBClient()
        db.save_script_characters(fallback_chars)
        return "Error occurred during character extraction. Saved fallback character information."

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