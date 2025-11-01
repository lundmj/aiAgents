from pathlib import Path
from agent import Agent
from agent_structures import AgentSequence
from dotenv import load_dotenv
load_dotenv()

def get_story_teller() -> Agent:
    """Create an AgentSequence that tells stories."""
    return Agent(
        Path('system_prompts/story_teller.md'),
        history_limit=3,
        model_name='gpt-4o',
    )

tellers = AgentSequence()

for _ in range(8):
    tellers.append(get_story_teller())

print("Give the story prompt (or 'exit' to exit):")

tellers.run()
