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
        self._client = AsyncOpenAI()
        self._model_name = model_name
        self._tool_box = tool_box
        self._prompt = prompt_file.read_text()
        self._history_limit = history_limit
        self._verbose = verbose
        self._system_msgs = [{'role': 'system', 'content': self._prompt}]
        if knowledge_names:
            from knowledge import load_knowledge_files
            self._system_msgs += load_knowledge_files(knowledge_names)

        self.reset()

    @property
    def full_history(self) -> list[dict]:
        return self._system_msgs + self._history

    def _get_user_input(self):
        if (user_msg := input('> ')) == "exit":
            return ""
        return user_msg

    async def _get_agent_response(self):
        return await self._client.responses.create(
            input=self.full_history,
            model=self._model_name,
            tools=self._tool_box.tools if self._tool_box else None,
        )

    def _handle_tool_calls(self, response_output):
        for item in response_output:
            if item.type == "function_call":
                if func := self._tool_box.get_tool_function(item.name):
                    result = func(**json.loads(item.arguments))
                    self._history.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result)
                    })
    
    def _impose_history_limit(self):
        excess = len(self._history) - self._history_limit
        if excess > 0:
            self._history = self._history[excess:]

    async def _chat_once_async(self, user_msg: str) -> str:
        """
        Send a single user message to the agent and return the response text.
        """
        self._history += [{'role': 'user', 'content': user_msg}]
        
        while True:
            response = await self._get_agent_response()
            self._history += response.output
            if not any(
                item.type == 'function_call' for item in response.output
            ): break
            self._handle_tool_calls(response.output)

        self._impose_history_limit()
        return response.output_text
    
    def reset(self):
        self._history = []
    
    async def run(self, callback=lambda *args: print('\nAI:', *args, end=f'\n{'-'*60}\n\n')):
        """
        Start an interaction loop with the agent.

        Inputs are read from stdin until an empty line or 'exit' is entered.
        """
        while user_msg := self._get_user_input():
            callback(await self._chat_once_async(user_msg))
    
    def chat_once(self, user_msg: str) -> str:
        """
        Synchronous wrapper for chat_once_async.
        """
        return asyncio.run(self._chat_once_async(user_msg))
