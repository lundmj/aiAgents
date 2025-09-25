import os
from agents import Agent, ModelSettings
from tools import *

def get_system_prompt(filename: str) -> str:
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, "system_prompts", filename)
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    parts = [line.strip() for line in lines if line.strip() != ""]
    return " ".join(parts)

calculator = Agent(
    name="Calculator",
    tools=[mul, add, sub, div, pow, set_status, get_status],
    instructions=get_system_prompt("calculator.md"),
    model='gpt-4',
    model_settings=ModelSettings(temperature=0, top_p=1),
)

chatter_1 = Agent(
    name="Chatter 1",
    instructions=get_system_prompt("conscious.md"),
    model='gpt-4',
)

chatter_2 = Agent(
    name="Chatter 2",
    instructions=get_system_prompt("conscious.md"),
    model='gpt-4',
)