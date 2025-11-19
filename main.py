import sys
import argparse
from pathlib import Path

import tools
from agentics_lundmj.agent import Agent

from dotenv import load_dotenv
load_dotenv()


def main(
    prompt_file: Path,
    history_limit: int,
    model_name: str = 'gpt-4.1',
    tool_box: str = None,
    verbose: bool = False,
):
    if tool_box:
        tool_box = getattr(tools, tool_box, None)
    Agent(
        prompt_file=prompt_file,
        history_limit=history_limit,
        model_name=model_name,
        tool_box=tool_box,
        verbose=verbose,
    ).run()
    print('\n' + "#"*60 + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', '-h', 
        action='help',
        help='show this help message and exit',
    )
    parser.add_argument('prompt_file',
        type=Path,
        help='path to system prompt file',
    )
    parser.add_argument('-m', '--model',
        type=str, default='gpt-4.1', dest='model',
        help='model name to use',
    )
    parser.add_argument('-t', '--tool-box',
        type=str, default=None, dest='tool_box',
        help='name of the tool box to use',
    )
    parser.add_argument('-v', '--verbose',
        action='store_true', dest='verbose',
        help='enable verbose output',
    )
    parser.add_argument('--history-limit', '-H',
        type=int, default=20, dest='history_limit',
        help='maximum number of past messages to keep in history',
    )

    args = parser.parse_args()

    main(
        Path(sys.argv[1]),
        args.history_limit,
        model_name=args.model,
        tool_box=args.tool_box,
        verbose=args.verbose,
    )
