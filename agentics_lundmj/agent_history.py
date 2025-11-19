from typing import Optional


class AgentHistory:
    """A class to manage the history of interactions for an AI agent."""

    def __init__(self, limit: Optional[int] = None):
        self._history = []
        self._limit = limit
    
    