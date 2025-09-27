from math import inf
import json
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
        self.prompt_user = True

    def append_history(self, message: dict):
        self._history.append(message)

    @property
    def full_history(self) -> list[dict]:
        return self._system_msgs + self._history

    def get_user_input(self):
        if (user_msg := input('User: ')) == "exit":
            return ""
        return user_msg

    async def get_agent_response(self):
        return await self.client.responses.create(
            input=self.full_history,
            model=self.model_name,
            tools=self.tool_box.tools,
        )

    def handle_tool_calls(self, response_output):
        for item in response_output:
            if item.type == "function_call":
                if self.verbose:
                    print(f'>>> Calling {item.name} with args {item.arguments}')
                if func := self.tool_box.get_tool_function(item.name):
                    result = func(**json.loads(item.arguments))
                    if self.verbose:
                        print(f'>>> {item.name} returned {result}')
                    self._history.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result)
                    })
    
    def impose_history_limit(self):
        excess = len(self._history) - self.history_limit
        if excess > 0:
            self._history = self._history[excess:]
    
    async def run(self):
        while True:
            if self.prompt_user:
                user_msg = self.get_user_input()
                if not user_msg:
                    break
                self.append_history(
                    {'role': 'user', 'content': user_msg}
                )
            response = await self.get_agent_response()
            self._history += response.output
            self.prompt_user = not any(item.type == 'function_call' for item in response.output)
            self.handle_tool_calls(response.output)
            if self.prompt_user or self.verbose:
                print('AI:', response.output_text)
            self.impose_history_limit()
