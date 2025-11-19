from dotenv import load_dotenv; load_dotenv()

import asyncio
from pathlib import Path
import speech_recognition as sr
from openai import AsyncOpenAI
from openai.helpers import LocalAudioPlayer

from agentics_lundmj.agent import Agent


def text_to_speech(*text) -> str:
    """
    Converts text to speech using OpenAI's TTS model.

    text: The text to convert to speech.

    Returns a message indicating success.
    """

    async def speak(text_to_speak: str) -> None:
        openai = AsyncOpenAI()
        async with openai.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice='nova',
            input=text_to_speak,
            instructions="Speak in a casual conversational tone.",
            response_format="pcm",
        ) as response:
            await LocalAudioPlayer().play(response)

    try:
        try:
            # Use the running event loop if available
            loop = asyncio.get_running_loop()
            asyncio.create_task(speak(" ".join(text)))
        except RuntimeError:
            # If no running loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(speak(" ".join(text)))
    except Exception as e:
        return f"Failure: {e}"
    return "Succeeded"

def audio_input() -> str:
    """
    Records audio from the system microphone and returns the transcribed text.

    Returns:
        str: Transcribed text from the recorded audio.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        # Adjust for ambient noise to improve recognition
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        input("Press Enter and start speaking...")
        audio = recognizer.listen(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        print("UnknownValueError encountered.")
        return "Sorry, I could not understand the audio."
    except sr.RequestError as e:
        print(f"RequestError encountered: {e}")
        return f"Could not request results; {e}"

guesser = Agent(
    Path("system_prompts/20_q.md"),
    model_name="gpt-4o-mini",
    history_limit=40,
)

def main():
    guesser.run(
        input_fn=audio_input,
        callback_fn=text_to_speech,
    )