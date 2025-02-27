# import agents
from agents.script_writer.tools import tools as story_tools
from agents.script_writer.prompt import story_writer_prompt, short_description
from agents.story_boarder.tools import tools as boarder_tools
from agents.story_boarder.prompt import story_boarder_prompt, short_description as boarder_description
from agents.dop.tools import tools as dop_tools
from agents.dop.prompt import dop_prompt, short_description as dop_description
from agents.audio.tools import tools as audio_tools
from agents.audio.prompt import audio_prompt, short_description as audio_description

# import mahilo
from mahilo import BaseAgent, AgentManager, ServerManager

def main():
    story_writer = BaseAgent(
        name="StoryWriterAgent",
        type="story_writer",
        description=story_writer_prompt,
        short_description=short_description,
        tools=story_tools,
    )

    story_boarder = BaseAgent(
        name="StoryBoarderAgent",
        type="story_boarder",
        description=story_boarder_prompt,
        short_description=boarder_description,
        tools=boarder_tools,
    )

    dop = BaseAgent(
        name="DOPAgent",
        type="dop",
        description=dop_prompt,
        short_description=dop_description,
        tools=dop_tools,
    )

    audio = BaseAgent(
        name="AudioAgent",
        type="audio",
        description=audio_prompt,
        short_description=audio_description,
        tools=audio_tools,
    )

    team = AgentManager()
    team.register_agent(story_writer)
    team.register_agent(story_boarder)
    team.register_agent(dop)
    team.register_agent(audio)
    # activate the agents
    story_writer.activate()
    story_boarder.activate()
    dop.activate()
    audio.activate()
    server = ServerManager(team)
    server.run()

if __name__ == "__main__":
    main()