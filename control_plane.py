# import agents
from agents.script_writer.tools import tools as story_tools
from agents.script_writer.prompt import story_writer_prompt, short_description

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

    team = AgentManager()
    team.register_agent(story_writer)

    # activate the base agent with no dependencies
    story_writer.activate()

    server = ServerManager(team)
    server.run()

if __name__ == "__main__":
    main()