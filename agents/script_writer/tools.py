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
    # # Initialize the agent with default settings
    # agent = ScriptWriterResearchAgent(
    #     model_id="o1",  # Default model
    #     max_steps=20,   # Default max steps
    #     verbosity_level=2  # Default verbosity
    # )
    
    # # Generate the script using the agent
    # script = agent.write_script(script_prompt)
    answer = """
CHICAGO NOCTURNE
A 1920s Prohibition-Era Thriller

TITLE: CHICAGO NOCTURNE

GENRE: Thriller, Historical Fiction

SETTING: 1920s Chicago, in the thick of Prohibition. The city teems with 
speakeasies, corruption, and gang rivalries, all overshadowed by the long arm 
of the law caught in murky ties.

MAIN CHARACTERS:
• SAM “THE BARTENDER” RUSSO
  - A quiet, introspective bartender at The Green Dahlia speakeasy. Ambitious, 
but consumed by moral conflicts.
• ROSA MANCINI
  - An undercover federal agent determined to bring down the city's most 
powerful crime syndicates.
• VINCENT “VINCENZO” CARUSO
  - A rising mob capo, charismatic and brutal, intent on controlling liquor 
distribution in Near West Side Chicago.
• “BIG MIKE” O'DONNELL
  - A rival gangster, ruthless in his pursuit of the north side's smuggling 
network.
• DETECTIVE FRANK POWELL
  - A veteran cop torn between his duty and the bribes that could secure his 
future. Deep down, he still believes in law and order.
• MAYOR HIGGINS
  - A city official rumored to be entangled with organized crime. He's eager to
keep the city's violence quiet to preserve his political power.

THEMES:
• The price of loyalty in a world of corruption.
• The haze between right and wrong when survival is at stake.
• The moral toll of living amid constant fear and violence.

STORYLINE (SCENE-BY-SCENE):

1) SCENE ONE – A WHISPER IN THE DARK
   LOCATION: Exterior streets, then interior of The Green Dahlia speakeasy.  
   TIME: Late evening.  
   ACTION: A quick montage of 1920s Chicago—a patchwork of smoky alleyways, 
rattling Model T Fords, and hush-hush transactions. We end up inside The Green 
Dahlia. Sam Russo works behind the bar, discreetly serving illegal liquor among
well-dressed patrons. Jazz flows through the sultry air. A faint sense of 
impending danger pervades; a hint that things could go wrong at any moment.

2) SCENE TWO – THE RAID
   LOCATION: The Green Dahlia, backstage storage.  
   TIME: Later that same night.  
   ACTION: Without warning, the establishment is subjected to a surprise police
raid. Rosa Mancini, posing as an agent with the Bureau of Prohibition, storms 
in with uniformed officers. Sam scrambles to hide crates of liquor. Rosa takes 
note of his quick wits and wonders if she can leverage him for information. 
Tension and chaos grip the patrons, but a timely bribe from the speakeasy's 
owner gets most officers to turn a blind eye—except for Rosa.

3) SCENE THREE – WARNING SHOTS
   LOCATION: Alley behind The Green Dahlia.  
   TIME: Immediately after the raid.  
   ACTION: Sam slips out the back to collect himself. Suddenly, Vincenzo Caruso
steps out of the shadows. He warns Sam that if the speakeasy's protection money
falters, unpleasant "accidents" might occur. Meanwhile, Big Mike's men lurk 
just out of sight, eavesdropping. A short, terse confrontation teases tensions 
between these rival gangs.

4) SCENE FOUR – ENTANGLEMENT
   LOCATION: A dimly-lit diner, across town.  
   TIME: The next morning.  
   ACTION: Detective Frank Powell summons Sam to the diner. He knows Sam 
witnessed more than he let on during the raid. With a mixture of paternal 
concern and mild threat, Powell demands Sam's cooperation. Sam, feeling 
cornered, says little. Detective Powell leaves with a grim handshake, making it
clear they'll speak again. Moments later, Rosa arrives, having tailed Powell. 
She quietly reveals she's working an undercover case, pressing Sam for inside 
information about Vincenzo. Sam remains wary, unsure whom to trust.

5) SCENE FIVE – UNMASKED INTENTIONS
   LOCATION: Mayor Higgins's lavish office.  
   TIME: Afternoon.  
   ACTION: We see a clandestine meeting: Vincenzo and Mayor Higgins discuss 
upcoming elections. Higgins promises to keep the police from "causing trouble" 
if Vincenzo keeps the violence under control. Rosa covertly snaps pictures from
a hidden vantage point. Suddenly, gunshots ring out. Someone tries to 
assassinate her. She narrowly escapes into a side corridor, breath ragged, 
exposed but alive.

6) SCENE SIX – THE TRUCE SHATTERS
   LOCATION: A rival speakeasy controlled by Vincenzo's men.  
   TIME: Night.  
   ACTION: Big Mike's men bomb Vincenzo's speakeasy in retaliation for 
perceived territory encroachment. The explosion is catastrophic, with flames 
and debris scattering. Innocent patrons are injured. This horrific act ignites 
an all-out gang war. Sam arrives too late; the sight of blood-spattered victims
rattles him. He realizes the gravity of the gang feud he's been dragged into.

7) SCENE SEVEN – CORNERED
   LOCATION: Sam's modest apartment, early morning.  
   TIME: The following day.  
   ACTION: Sam awakens to a knock on his door—Detective Powell again. This 
time, Powell begs Sam for any lead that might stop the violence. Sam hesitates,
caught between terror of retribution and a pang of conscience. Later, Vincenzo 
arrives unannounced. He demands Sam's help in smuggling weapons across town. 
Sam is now squeezed from both ends, with nowhere left to hide.

8) SCENE EIGHT – SHOWDOWN AT THE GREEN DAHLIA
   LOCATION: The Green Dahlia (closed to the public for now).  
   TIME: Late night.  
   ACTION: Both gang factions converge for a high-stakes negotiation that 
quickly turns into a firefight. Rosa bursts in, determined to expose the 
mayor's collusion. Detective Powell attempts to maintain order, but shots ring 
out in the dark. Sam, forced to pick a side, uses his knowledge of the 
speakeasy's secret tunnels to help Rosa corner Mayor Higgins and Vincenzo. 
Before the final bullet is fired, Sam chooses to stand with Rosa.

9) SCENE NINE – AFTERMATH
   LOCATION: Chicago courthouse steps, by early morning light.  
   TIME: Days later.  
   ACTION: Vincenzo is arrested, Big Mike goes underground, and Mayor Higgins 
faces public scandal. Rosa works with prosecutors, while Sam serves as a key 
witness. Detective Powell, battered but hopeful, vows to keep fighting 
corruption. Sam stands on the courthouse steps as dawn breaks, unsure if he'll 
ever feel safe. But for the first time, he sees a glimmer of hope that perhaps 
he can live a life outside the city's lethal shadow.

END NOTE:
The city remains battered and bruised, haunted by the ghosts of gang violence 
and political corruption. Yet, even in the hush of the early morning, the faint
strains of jazz can still be heard through hidden doorways. Life in Chicago 
marches on, accompanied by the promise that no matter how deep the corruption 
runs, courage can still pierce the veil of darkness."""

    # make file if not exists
    if not os.path.exists("data/script_writer"):
        os.makedirs("data/script_writer")

    # write it to a file
    with open("data/script_writer/script.txt", "w") as f:
        f.write(answer)
    
    # Extract and save characters
    extract_and_save_characters(answer)
    
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