import asyncio
import sys
import argparse
import json
from pathlib import Path

from openai import AsyncOpenAI
import tools as tools_module


def get_selected_tools(tool_names: list[str]) -> dict:
    """Validate tool names and return a dict of name->callable for available tools in tools.py."""
    selected: dict[str, callable] = {}
    for name in tool_names:
        if not name:
            continue
        if not hasattr(tools_module, name):
            print(f"Warning: tool '{name}' not found in tools.py", file=sys.stderr)
            continue
        fn = getattr(tools_module, name)
        if callable(fn):
            selected[name] = fn
        else:
            print(f"Warning: attribute '{name}' in tools.py is not callable", file=sys.stderr)
    return selected


def parse_json_tool_call(text: str) -> dict | None:
    """
    Try to parse a JSON tool call from assistant output.
    Accepts either a pure JSON string or JSON embedded in surrounding text.
    Expected format: {"tool":"name","args":[...]}.
    Returns the parsed dict or None.
    """
    if not text or not isinstance(text, str):
        return None
    s = text.strip()
    # First try whole-string parse
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict) and 'tool' in parsed and 'args' in parsed:
            return parsed
        return None
    except json.JSONDecodeError:
        # Attempt to find a JSON object inside the text
        start = s.find('{')
        end = s.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        snippet = s[start:end+1]
        try:
            parsed = json.loads(snippet)
            if isinstance(parsed, dict) and 'tool' in parsed and 'args' in parsed:
                return parsed
        except Exception:
            return None
    except Exception:
        return None
    return None


def execute_tool_call(parsed: dict, selected_tools: dict, system_messages: list) -> dict | None:
    """
    Execute a parsed tool call against selected_tools. Append a system message with the result.
    Returns a dict with execution info or None if tool not available.
    """
    tool_name = parsed.get('tool')
    args = parsed.get('args', [])
    if tool_name not in selected_tools:
        print(f"Tool '{tool_name}' was requested but not enabled.")
        return None
    tool_fn = selected_tools[tool_name]
    try:
        result = tool_fn(*args)
    except Exception as te:
        result = f"ERROR: tool execution failed: {te}"
    log_line = f"[tool call] {tool_name}({args}) -> {result}"
    print(log_line)
    system_messages.append({'role': 'system', 'content': log_line})
    return {'tool': tool_name, 'args': args, 'result': result, 'log': log_line}


def load_knowledge_files(knowledge_names: list[str]) -> list[dict]:
    messages: list[dict] = []

    def add_file(file_path: Path):
        safe = file_path.name
        try:
            text = file_path.read_text(encoding='utf-8')
            parts = [line.strip() for line in text.splitlines() if line.strip() != ""]
            content = " ".join(parts)
            messages.append({'role': 'system', 'content': f"[knowledge: {safe}] {content}"})
        except Exception as e:
            print(f"Warning: failed to read knowledge file {file_path}: {e}", file=sys.stderr)

    for name in knowledge_names:
        if not name:
            continue
        file_path = Path(name)
        if not file_path.exists():
            print(f"Warning: knowledge file not found: {name}", file=sys.stderr)
            continue
        if file_path.is_dir():
            for subfile in file_path.rglob('*'):
                if subfile.is_file():
                    add_file(subfile)
        elif file_path.is_file():
            add_file(file_path)
        else:
            print(f"Warning: {name} is neither a file nor a directory", file=sys.stderr)
    return messages


async def main(prompt_file: Path, history_len: int, model_name: str, tool_names: list[str], knowledge_names: list[str], reasoning: str | None = None):
    client = AsyncOpenAI()
    # base system prompt (from prompt_file) plus any knowledge files
    system_messages = [
        {'role': 'system', 'content': prompt_file.read_text()}
    ] + load_knowledge_files(knowledge_names)
    history_messages = []

    # Collect tool callables using helper
    selected_tools = get_selected_tools(tool_names)

    while True:
        # Get user input
        user_msg = input("# ")
        if user_msg.lower() in ["exit", "quit"]:
            break
        history_messages.append({'role': 'user', 'content': user_msg})

        # Build messages: system messages always included plus recent history
        messages_to_send = system_messages + history_messages
        try:
            response = await client.responses.create(
                input=messages_to_send,
                model=model_name,
                reasoning={'effort': reasoning} if reasoning else None,
            )
        except Exception as e:
            print(f"Error during API call: {e}", file=sys.stderr)
            continue

        assistant_text = response.output_text.strip()
        history_messages.append({'role': 'assistant', 'content': assistant_text})

        # Use helper to recognize and execute tool calls.
        # If a tool is requested, execute it and allow the model to produce a follow-up response
        # that can reason about the tool's result. Limit iterations to avoid infinite loops.
        parsed = parse_json_tool_call(assistant_text)
        max_tool_iters = 6
        iters = 0
        while parsed is not None and iters < max_tool_iters:
            iters += 1
            execute_tool_call(parsed, selected_tools, system_messages)

            # Re-query the model so it can incorporate the tool output into a new reply
            try:
                follow = await client.responses.create(
                    input=system_messages + history_messages,
                    model=model_name,
                    reasoning={'effort': reasoning} if reasoning else None,
                )
            except Exception as e:
                print(f"Error during API call after tool execution: {e}", file=sys.stderr)
                break

            assistant_text = follow.output_text.strip()
            history_messages.append({'role': 'assistant', 'content': assistant_text})

            # Check for another tool call in the follow-up reply
            parsed = parse_json_tool_call(assistant_text)

        # Print assistant text for visibility (final reply after any tool loop)
        print(assistant_text, end="\n\n")

        # Trim stored history_messages to avoid unbounded growth while keeping the most recent `history_len` items.
        if history_len is not None and history_len > 0:
            history_messages = history_messages[-history_len:]


## Program entry ##

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '--help', '-?',
        action='help',
        help='show this help message and exit'
    )
    parser.add_argument(
        'prompt_file',
        type=Path,
        help='path to system prompt file'
    )
    parser.add_argument(
        '-h', '--history',
        type=int,
        default=20,
        dest='history',
        help='history length (positive integer). Example: -h 3 keeps the last 3 messages'
    )
    parser.add_argument(
        '-m', '--model',
        type=str,
        default='gpt-4o-mini',
        dest='model',
        help='model name to use'
    )
    parser.add_argument(
        '-t', '--tools',
        type=str,
        default='',
        dest='tools',
        help='comma-separated list of tool function names from tools.py to enable (e.g. add,mul,read_file)'
    )
    parser.add_argument(
        '-k', '--knowledge',
        type=str,
        default='',
        dest='knowledge',
        help='comma-separated list of filenames in reference/ to include as knowledge'
    )
    parser.add_argument(
        '-r', '--reasoning',
        type=str,
        default='',
        dest='reasoning',
        help='reasoning to use for the model'
    )

    args = parser.parse_args()

    if args.history <= 0:
        print("Error: history length must be a positive integer.", file=sys.stderr)
        sys.exit(1)

    tool_list = [t.strip() for t in args.tools.split(',')] if args.tools else []
    knowledge_list = [k.strip() for k in args.knowledge.split(',')] if args.knowledge else []

    asyncio.run(main(args.prompt_file, args.history, args.model, tool_list, knowledge_list, args.reasoning if args.reasoning else None))
