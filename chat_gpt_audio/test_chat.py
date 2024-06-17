# Copyright 2023 Figure AI, Inc

from __future__ import annotations

import logging
import os
import time

import openai
import requests
from openai import OpenAI
from audio import AudioPlayer

VOICE_CLONE_URL = "https://api.openai.com/v1/audio/synthesize"
VOICE_CLONE_HEADERS = {
    "Authorization": "Bearer sk-proj-FW1HvpkuoqsuuVnvm7FTT3BlbkFJOsOE2kux5mP5nkW89jRy" # mine
}

logger = logging.getLogger(__name__)


from chat import ChatAgent

if __name__ == "__main__":

    openai_api_key = "sk-proj-FW1HvpkuoqsuuVnvm7FTT3BlbkFJOsOE2kux5mP5nkW89jRy" # Mine

    audio = AudioPlayer(device='MacBook Pro Speakers')
    chat_agent = ChatAgent(audio=audio, openai_api_key=openai_api_key)

    while True:
        print("ask a question NOWWW!!")
        chat_agent.chat()
        print("Iteration finished. Sleeping for 5 seconds")
        time.sleep(5.0)

