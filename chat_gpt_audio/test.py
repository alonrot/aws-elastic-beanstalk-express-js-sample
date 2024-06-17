# Copyright 2023 Figure AI, Inc

from __future__ import annotations

import logging
import os

import openai
import requests
from openai import OpenAI
from audio import AudioPlayer

GLASS_SOUND = "python_modules/manipulation/assets/sounds/glass.wav"
VOICE_CLONE_URL = "https://api.openai.com/v1/audio/synthesize"
VOICE_CLONE_HEADERS = {
    "Authorization": "Bearer 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"
}

logger = logging.getLogger(__name__)



if __name__ == "__main__":

    openai_api_key = "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"

    openai.api_key = openai_api_key
    os.environ["OPENAI_API_KEY"] = openai.api_key

    oai_client = OpenAI()
    logger.info("Created OpenAI client.")




    # completion = self.oai_client.chat.completions.create(
    #     model="gpt-4", messages=self._messages, seed=1234
    # )


    # self.oai_client.chat.completions.create(
    #     model="gpt-3.5-turbo",
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": "You are a helpful assistant.'",
    #         },
    #         {
    #             "role": "user",
    #             "content": "What is 1+1?.",
    #         },
    #     ],
    # )
    # return True


    # mp3_path = self._chat_dir / f"{len(self._audio_files)}_gpt.mp3"
    # mp3_path = "/Users/alonrot/artistic/chat_gpt_audio/dummy2.mp3"
    mp3_path = "/Users/alonrot/artistic/chat_gpt_audio/mama/merged_audio.mp3"
    mp3_path_save = "/Users/alonrot/artistic/chat_gpt_audio/mama/merged_audio_response.mp3"


    # with open(mp3_path.parent / f"{mp3_path.stem}.txt", "w") as f:
    #     f.write(response_text)

    # if voice != "jared":
    #     # Convert text response to speech
    #     with self.oai_client.audio.speech.with_streaming_response.create(
    #         model="tts-1-hd", voice=voice, input=response_text
    #     ) as response_audio:
    #         response_audio.stream_to_file(str(mp3_path))
    # else:
    response_text = "Hola, os envío recuerdos desde aquí, desde los Estados Unidos. Y nada, un besooo, adióooos."
    data = {
        "model": "tts-1-hd",
        "text": response_text,
        "speed": "0.9",
        "response_format": "mp3",
    }
    with open(mp3_path, "rb") as f:
        files = {"reference_audio": f}
        response = requests.post(
            VOICE_CLONE_URL, headers=VOICE_CLONE_HEADERS, data=data, files=files
        )
        if response.status_code == 200:
            with open(mp3_path_save, "wb") as out:
                out.write(response.content)
            logger.info(f"Audio saved as {mp3_path_save}")
        else:
            logger.info(f"Error: {response.status_code} - {response.text}")

    # Play the response
    # self._audio_files.append(mp3_path)
    audio = AudioPlayer(device='MacBook Pro Speakers')
    audio.play(mp3_path_save)
