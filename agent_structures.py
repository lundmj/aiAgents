from agent import AIInteractable


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
