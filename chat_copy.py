import asyncio
import sys
import argparse
from pathlib import Path

from openai import AsyncOpenAI


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


async def main(
    prompt_file: Path,
    history_len: int,
    model_name: str,
    knowledge_names: list[str],
    reasoning: str | None = None
):
    client = AsyncOpenAI()
    # base system prompt (from prompt_file) plus any knowledge files
    system_messages = [
        {'role': 'system', 'content': prompt_file.read_text()}
    ] + load_knowledge_files(knowledge_names)
    history_messages = []

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

        # Print assistant text for visibility (final reply)
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

    knowledge_list = [k.strip() for k in args.knowledge.split(',')] if args.knowledge else []

    asyncio.run(main(args.prompt_file, args.history, args.model, knowledge_list, args.reasoning if args.reasoning else None))
