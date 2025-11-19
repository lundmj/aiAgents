from collections import deque
import json
import functools
from pathlib import Path
from openai import OpenAI
from typing import Callable

from .tool_box import ToolBox
from .agent_base import AIInteractable


class Agent(AIInteractable):
    """
    A self-sufficient AI agent that can be interacted with via a chat interface.

    - Calling `run()` starts an interaction loop reading from stdin.
    - Calling `chat_once(msg)` sends a single message and returns the response.
    - Calling `reset()` clears all chat history.

    Both `run` and `chat_once` track history up to `history_limit` messages.
    """

    def __init__(self,
        prompt_file: Path | str,
        history_limit: int = 20,
        history_limit_strict: bool = False,
        model_name: str = 'gpt-4.1',
        tool_box: ToolBox = None,
        helper_agents: list['Agent'] = [],
        description: str = '',
        verbose: bool = False,
    ):
        self.client = OpenAI()
        self._history_limit_strict = history_limit_strict
        self._model_name = model_name
        self._tool_box = tool_box
        self._helper_agents = helper_agents
        self._prompt = Path(prompt_file).read_text()
        self._history_limit = history_limit
        self._description = description
        self._verbose = verbose
        self._system_messages = [{ 'role': 'system', 'content': self._prompt }]

        self._add_helper_agents()
        self.reset()

    def full_history(self) -> list[dict]:
        return self._system_messages + list(self._history)

    def _add_helper_agents(self):
        if not self._helper_agents: return
        agent_tool_box = ToolBox()
        for i, agent in enumerate(self._helper_agents, start=1):
            name, wrapper = self._build_agent_tool(agent, i)
            agent_tool_box.tool(wrapper, name=name)
        self._tool_box = agent_tool_box | self._tool_box

    def _build_agent_tool(self, agent: "Agent", index: int) -> tuple[str, Callable]:
        unique_name = f"{agent.__class__.__name__}_chat_once_{index}"
        desc_suffix = f"\n\nDescription: {agent._description}" if agent._description else ""

        @functools.wraps(agent.chat_once)
        def wrapper(*args, **kwargs):
            return agent.chat_once(*args, **kwargs)
        wrapper.__doc__ = (agent.chat_once.__doc__ or "") + desc_suffix

        return unique_name, wrapper

    def _get_agent_response(self):
        return self.client.responses.create(
            input=self.full_history(),
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
    
    def reset(self):
        self.shallow_reset()
        for agent in self._helper_agents:
            agent.reset()
    
    def shallow_reset(self):
        if self._history_limit_strict:
            self._history = deque(maxlen=self._history_limit)
        else:
            self._history = []
    
    def _trim_history(self):
        if self._history_limit_strict:
            return  # deque already enforces limit
        self._history = self._history[-self._history_limit:]
    
    def chat_once(self, msg: str) -> str:
        """
        Send a message to the agent.

        Returns the agent's response text.
        """
        self._history.append({ 'role': 'user', 'content': msg })
        while True: # loop to accommodate tool calls
            response = self._get_agent_response()
            try:
                self._history.extend(response.output)
            except TypeError:
                self._history.append(response.output)
            if not any(
                item.type == 'function_call' for item in response.output
            ): break
            self._handle_tool_calls(response.output)
        self._trim_history()
        return response.output_text
    

class AgentSequence(AIInteractable):
    """
    A sequence of AIInteractable objects that can be treated as a single interactable.

    Input is first sent to the first interactable, and its output is passed as input to the next,
    and so on. The last interactable's output is returned as the final output.
    """

    def __init__(self, *interactables: AIInteractable):
        if not all(
            isinstance(interactable, AIInteractable) for interactable in interactables
        ): raise TypeError("All elements must be instances of AIInteractable")
        self.interactables = list(interactables)

    def __getitem__(self, index):
        return self.interactables[index]

    def __len__(self):
        return len(self.interactables)
    
    def __iter__(self):
        return iter(self.interactables)
    
    def __contains__(self, interactable):
        return interactable in self.interactables
    
    def __eq__(self, other):
        if not isinstance(other, AgentSequence):
            return False
        return self.interactables == other.interactables

    def append(self, interactable):
        self.interactables.append(interactable)

    def remove(self, interactable):
        self.interactables.remove(interactable)
    
    def chat_once(self, msg: str) -> str:
        for interactable in self.interactables:
            msg = interactable.chat_once(msg)
            print(f"[AgentSequence] Intermediate output: {msg}")
        return msg

    def reset(self):
        for interactable in self.interactables:
            interactable.reset()
