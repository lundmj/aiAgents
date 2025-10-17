import json
import functools
from pathlib import Path
from openai import OpenAI
from param import Callable as function

from tool_box import ToolBox


class Agent:
    """
    A self-sufficient AI agent that can be interacted with via a chat interface.

    - Calling `run()` starts an interaction loop reading from stdin.
    - Calling `chat_once(user_msg)` sends a single message and returns the response.
    - Calling `reset()` clears all chat history.

    Both `run` and `chat_once` track history up to `history_limit` messages.
    """

    def __init__(self,
        prompt_file: Path,
        history_limit: int,
        model_name: str = 'gpt-4.1',
        tool_box: ToolBox = None,
        helper_agents: list['Agent'] = [],
        description: str = 'A helpful assistant.',
        verbose: bool = False,
    ):
        self.client = OpenAI()
        self._model_name = model_name
        self._tool_box = tool_box
        self._helper_agents = helper_agents
        self._prompt = prompt_file.read_text()
        self._history_limit = history_limit
        self._description = description
        self._verbose = verbose
        self._system_messages = [{ 'role': 'system', 'content': self._prompt }]

        self._add_helper_agents()
        self.reset()

    @property
    def full_history(self) -> list[dict]:
        return self._system_messages + self._history

    def _add_helper_agents(self):
        if not self._helper_agents: return
        agent_tool_box = ToolBox()
        for i, agent in enumerate(self._helper_agents, start=1):
            # Build a unique tool name per helper agent to avoid collisions
            unique_name = f"{agent.__class__.__name__}_chat_once_{i}"
            desc_suffix = f"\n\nDescription: {agent._description}"

            def make_wrapper(bound_method, doc):
                @functools.wraps(bound_method)
                def wrapper(*args, **kwargs):
                    return bound_method(*args, **kwargs)
                try:
                    wrapper.__doc__ = (bound_method.__doc__ or "") + doc
                except Exception:
                    pass
                return wrapper

            wrapper = make_wrapper(agent.chat_once, desc_suffix)
            agent_tool_box.tool(wrapper, name=unique_name)
        self._tool_box = agent_tool_box | self._tool_box

    def _get_user_input(self):
        if (user_msg := input('> ')) == "exit":
            return ""
        return user_msg

    def _get_agent_response(self):
        return self.client.responses.create(
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

    def reset(self):
        self._history = []
    
    def run(self,
        callback: function = lambda *args: print(
            '\nAI:', *args, end=f'\n{'-'*60}\n\n'
        )
    ):
        """
        Start an interaction loop with the agent.

        Inputs are read from stdin until an empty line or 'exit' is entered.
        """
        while user_msg := self._get_user_input():
            callback(self.chat_once(user_msg))
    
    def chat_once(self, user_msg: str) -> str:
        """
        Send a message to the agent.

        Returns the agent's response text.
        """
        self._history += [{ 'role': 'user', 'content': user_msg }]
        
        while True:
            response = self._get_agent_response()
            self._history += response.output
            if not any(
                item.type == 'function_call' for item in response.output
            ): break
            self._handle_tool_calls(response.output)

        self._impose_history_limit()
        return response.output_text
    

