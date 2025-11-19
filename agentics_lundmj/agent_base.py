from typing import Optional, Callable

class AIInteractable:
    """An interface for AI agents that can interact with users."""

    def _get_user_input(self) -> str:
        if (msg := input('> ')) == "exit":
            return ""
        return msg
    
    def _print_agent_response(self, *args):
        print('\nAI:', *args) 
        print('-'*60 + '\n')   

    def run(self,
        input_fn: Optional[Callable] = None,
        callback_fn: Optional[Callable] = None
    ):
        """
        Start an interaction loop with the agent.

        Inputs are read from stdin until an empty line or 'exit' is entered.
        """
        callback_fn = callback_fn or self._print_agent_response
        input_fn = input_fn or self._get_user_input

        try:
            while msg := input_fn():
                callback_fn(self.chat_once(msg))
        except KeyboardInterrupt:
            print('\nRun interrupted by user (KeyboardInterrupt)')

    def chat_once(self, msg: str) -> str:
        raise NotImplementedError

    def reset(self):
        raise NotImplementedError
