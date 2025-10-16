from pathlib import Path
from tools import calendar_tool_box, email_tool_box
from agent import Agent

email_agent = Agent(
    Path('system_prompts/email_assistant.md'),
    6,
    tool_box=email_tool_box,
    description='An assistant that can send emails to any address.'
)

calendar_agent = Agent(
    Path('system_prompts/calendar_assistant.md'),
    6,
    tool_box=calendar_tool_box,
    description='An assistant that can manage a calendar.'
)

delegator_agent = Agent(
    Path('system_prompts/assistant_delegator.md'),
    20,
    helper_agents=[email_agent, calendar_agent],
    description='An assistant that delegates tasks to other agents.',
)