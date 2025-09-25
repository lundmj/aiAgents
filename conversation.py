import asyncio
import logging
from agents import Runner
from my_agents import chatter_1, chatter_2

# Log to conversation.log with timestamps
logging.basicConfig(
    filename="conversation.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

def check_if_quit(message):
    if "I would like to end this session" in message:
        logging.info("Session end requested. Exiting.")
        exit(0)

async def main():
    topic = input("Enter topic: ")
    agents = [chatter_1, chatter_2]
    message = f"User: I want you two to discuss this topic: {topic}"

    logging.info(f"Starting conversation on topic: {topic}")
    logging.info(f"User: {message}")

    while True:
        for agent in agents:
            message = (await Runner.run(agent, message)).final_output
            logging.info(f"{agent.name}: {message}")
            check_if_quit(message)

if __name__ == "__main__":
    asyncio.run(main())
