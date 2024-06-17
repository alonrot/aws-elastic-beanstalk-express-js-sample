# Copyright 2023 Figure AI, Inc

from __future__ import annotations

import logging
import os
import time

import openai
import requests
from openai import OpenAI
from audio import AudioPlayer

GLASS_SOUND = "python_modules/manipulation/assets/sounds/glass.wav"
VOICE_CLONE_URL = "https://api.openai.com/v1/audio/synthesize"
VOICE_CLONE_HEADERS = {
    # "Authorization": "Bearer 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" # Figure AI
    "Authorization": "Bearer sk-proj-earxH8UQPGreMKyDyAcrT3BlbkFJvCFjejhpHYumPrZidspp" # Figure AI
}

logger = logging.getLogger(__name__)


from chat import ChatAgent

if __name__ == "__main__":

    # openai_api_key = "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" # Figure AI

    openai_api_key = "sk-proj-earxH8UQPGreMKyDyAcrT3BlbkFJvCFjejhpHYumPrZidspp" # Mine

    audio = AudioPlayer(device='MacBook Pro Speakers')
    chat_agent = ChatAgent(audio=audio, openai_api_key=openai_api_key)

    while True:
        print("ask a question NOWWW!!")
        chat_agent.chat()
        print("Iteration finished. Sleeping for 5 seconds")
        time.sleep(5.0)

