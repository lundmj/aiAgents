import asyncio
import json
import sys
import argparse
from pathlib import Path
from openai import AsyncOpenAI
from tools import calendar_tool_box, email_tool_box
from knowledge import load_knowledge_files

async def main(
    prompt_file: Path,
    model_name: str = 'gpt-4.1',
    knowledge_names: list[str] = None
):
    TOOL_BOX = email_tool_box
    # TOOL_BOX = calendar_tool_box
    client = AsyncOpenAI()
    prompt = prompt_file.read_text()

    # base system prompt plus any knowledge files
    system_msgs = [{'role': 'system', 'content': prompt}]
    if knowledge_names:
        system_msgs += load_knowledge_files(knowledge_names)

    history = system_msgs.copy()
    prompt_user = True

    while True:
        if prompt_user:
            if (user_msg := input('User: ')) == "exit":
                break

            history.append({
                'role': 'user', 'content': user_msg
            })

        response = await client.responses.create(
            input=history,
            model=model_name,
            tools=TOOL_BOX.tools
        )

        history += response.output

        prompt_user = not any(item.type == 'function_call' for item in response.output)

        for item in response.output:
            if item.type == "function_call":
                print(f'>>> Calling {item.name} with args {item.arguments}')
                if func := TOOL_BOX.get_tool_function(item.name):
                    result = func(**json.loads(item.arguments))

                    print(f'>>> {item.name} returned {result}')
                    history.append({
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result)
                    })

        print('AI:', response.output_text)

        if 'DONE' in response.output_text:
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', '-?', action='help', help='show this help message and exit')
    parser.add_argument('prompt_file', type=Path, help='path to system prompt file')
    parser.add_argument('-m', '--model', type=str, default='gpt-5-mini', dest='model',
                        help='model name to use')
    parser.add_argument('-k', '--knowledge', type=str, default='', dest='knowledge',
                        help='comma-separated list of filenames or directories to include as knowledge')

    args = parser.parse_args()

    knowledge_list = [k.strip() for k in args.knowledge.split(',')] if args.knowledge else []

    asyncio.run(main(Path(sys.argv[1]), args.model, knowledge_list))
