import asyncio
import sys
import argparse
from pathlib import Path
from tools import calendar_tool_box, email_tool_box
from agent import Agent

TOOL_BOX = calendar_tool_box

async def main(
    prompt_file: Path,
    history_limit: int,
    model_name: str = 'gpt-4.1',
    verbose: bool = False,
):
    agent = Agent(
        prompt_file=prompt_file,
        history_limit=history_limit,
        model_name=model_name,
        tool_box=TOOL_BOX,
        verbose=verbose,
    )
    await agent.run()
    print('\n' + "#"*60 + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', '-?', 
        action='help',
        help='show this help message and exit',
    )
    parser.add_argument('prompt_file',
        type=Path,
        help='path to system prompt file',
    )
    parser.add_argument('-m', '--model',
        type=str, default='gpt-5-mini', dest='model',
        help='model name to use',
    )
    parser.add_argument('-v', '--verbose',
        action='store_true', dest='verbose',
        help='enable verbose output',
    )
    parser.add_argument('--history-limit',
        type=int, default=20, dest='history_limit',
        help='maximum number of past messages to keep in history',
    )

    args = parser.parse_args()

    asyncio.run(main(
        Path(sys.argv[1]),
        args.history_limit,
        model_name=args.model,
        verbose=args.verbose,
    ))
