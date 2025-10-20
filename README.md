# Personal Project: AI Agent Framework

A modular and extensible framework for building AI agents capable of interacting with users, managing tools, and delegating tasks to helper agents. The project is designed for flexibility, maintainability, and ease of integration with tools.

## Key Features

- **Agent Class**: A self-sufficient AI agent with chat capabilities, history management, and tool integration.
- **ToolBox**: A utility for registering and managing tools with strict JSON schemas.
- **Multi-Agent Systems**: Agents can delegate tasks to other helper agents, enabling complex workflows and collaborative problem-solving.
- **Extensibility**: Easily add new tools, including to integrate with external APIs.

## Repository Structure

1. **`agent.py`**
   - Implements the `Agent` class, which serves as the core of the framework.
   - Features:
     - Chat interface with history management using `deque`.
     - Integration with tools and helper agents.
     - Graceful handling of user interruptions (`KeyboardInterrupt`).
     - Modularized helper-agent tool registration.

2. **`tool_box.py`**
   - Provides the `ToolBox` class for managing tools.
   - Features:
     - Tool registration with JSON schema validation.
     - Logging of tool calls and results.
     - Support for merging multiple `ToolBox` instances.

3. **`tools.py`**
   - A compilation of example tools for integration with the framework.
   - Includes tools for tasks like managing Google Calendar events and sending emails.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Required Python packages (install via `pip`):
  - `openai`
  - `google-auth`
  - `google-auth-oauthlib`
  - `google-api-python-client`
  - `python-dotenv`

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lundmj/aiAgents.git
   cd aiAgents
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### `main` Usage

1. Run the agent with a system prompt:
   ```bash
   python main.py system_prompts/calendar_assistant.md -t calendar_tool_box
   ```

2. Use the `-h` flag for help:
   ```bash
   python main.py -h
   ```

### Defining Your Own
1. Agent
   - Create an instance of the `Agent` class in `agent.py`.
2. Tool
   - Import `ToolBox` into the file in which you want to define tools (see `tools.py`). Create an instance of the tool box. 
   - Write a function that you want your agent to be able to call.
     - The parameters need to be strings or a numeric type.
     - Annotate the types of the parameters, give the parameters clear names, and define a return type (typically `str`). The `ToolBox` will enable the agent to read and understand this function signature.
     - Write a simple docstring explaining the functionality of the tool, using `"""` notation. `ToolBox` will also help the agent read this as an explanation of the tool.
   - Decorate the function with `@<tool_box>.tool` to store the tool in the tool box.
     - Replace `<tool_box>` with the variable name of your tool box.
   - Any number of tools can go in a tool box, and by stacking decorations, you can put a tool in any number of tool boxes.

## Example Files

### System Prompts

The `system_prompts` folder contins some example prompts to give an AI agent. These are what you provide a `Path` to when instantiating an agent.

### Delegator Example

The file `delegator.py` is an example of three agents:
- `delegator_agent` uses a reasoning model and has the other two agents provided to it as tools. It is instructed to simply carry out tasks, with knowledge that it may need to delegate. Notice that its system prompt contains no direction as to which agents it can delegate to; it deduces that from the agents it gets.
- `calendar_agent` and `email_agent` are non-reasoning models (using `gpt-4.1`) that are instructed to handle their various tasks. They are provided their own set of tools in their tool boxes, which are independent of each other and the delegator agent above them.
