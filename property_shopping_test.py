from dotenv import load_dotenv
load_dotenv()

from agentics_lundmj.agent import Agent
from agentics_lundmj.tool_box import ToolBox
tb = ToolBox()

log_grade = print

@tb.tool
def grade_response(grade: float) -> str:
    """
    Logs the grade provided.

    grade: A float between 0 and 10 representing the grade.

    Returns a message indicating success.
    """
    if not (0.0 <= grade <= 10.0):
        return "Failure: Grade must be between 0 and 10."
    log_grade(grade)
    return "Succeeded"

models = [
    'gpt-4.1',
    'gpt-4o-mini',
    'gpt-5-mini',
    'gpt-5-nano',
]

grader_model = 'gpt-5-mini'

for model in models:
    shopper = Agent(
        prompt_file='system_prompts/property_shopper.md',
        history_limit=10,
        model_name=model,
    )
    grader = Agent(
        prompt_file='system_prompts/shopper_grader.md',
        history_limit=10,
        model_name=grader_model,
        tool_box=tb,
    )
    interest_message = shopper.chat_once("Email")
    print(interest_message)
    grader.chat_once(interest_message)
