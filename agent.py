import json
import asyncio
from pathlib import Path

from openai import AsyncOpenAI

from tool_box import ToolBox


class Agent:
    def __init__(self,
        prompt_file: Path,
        history_limit: int,
        model_name: str = 'gpt-4.1',
        knowledge_names: list[str] = None,
        tool_box: ToolBox = None,
        verbose: bool = False,
    ):
        self.client = AsyncOpenAI()
        self.model_name = model_name
        self.tool_box = tool_box
        self.prompt = prompt_file.read_text()
        self.history_limit = history_limit
        self.verbose = verbose
        self._system_msgs = [{'role': 'system', 'content': self.prompt}]
        if knowledge_names:
            from knowledge import load_knowledge_files
            self._system_msgs += load_knowledge_files(knowledge_names)

        self.reset()

    def reset(self):
        self._history = []
    
    def print_if_verbose(self, message: str):
        if self.verbose:
            print(message)

    @property
    def full_history(self) -> list[dict]:
        return self._system_msgs + self._history

    def get_user_input(self):
        if (user_msg := input('> ')) == "exit":
            return ""
        return user_msg

    async def get_agent_response(self):
        return await self.client.responses.create(
            input=self.full_history,
            model=self.model_name,
            tools=self.tool_box.tools if self.tool_box else None,
        )

    def handle_tool_calls(self, response_output):
        for item in response_output:
            if item.type == "function_call":
                self.print_if_verbose(f'>>> Calling {item.name} with args {item.arguments}')
                if func := self.tool_box.get_tool_function(item.name):
                    result = func(**json.loads(item.arguments))
                    self.print_if_verbose(f'>>> {item.name} returned {result}')
                    self._history.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result)
                    })
    
    def impose_history_limit(self):
        excess = len(self._history) - self.history_limit
        if excess > 0:
            self._history = self._history[excess:]

    async def run(self, response_fn=lambda *args: print('\n', *args, end=f'\n{'-'*60}\n\n')):
        """
        Start an interaction loop with the agent.

        Inputs are read from stdin until an empty line or 'exit' is entered.
        """
        while user_msg := self.get_user_input():
            response_fn('AI:', await self.chat_once(user_msg))
    
    async def chat_once(self, user_msg: str) -> str:
        """
        Send a single user message to the agent and return the response text.
        """
        self._history += [{'role': 'user', 'content': user_msg}]
        
        while True:
            response = await self.get_agent_response()
            self._history += response.output
            if not any(
                item.type == 'function_call' for item in response.output
            ): break
            self.handle_tool_calls(response.output)

        self.impose_history_limit()
        return response.output_text
