# Copyright 2023 Figure AI, Inc

from __future__ import annotations

import logging
import os
import pathlib
import random
import time
from datetime import datetime
from typing import Literal, Optional, Protocol

# import hydra
# import numpy as np
# import numpy.typing as npt
import openai
import requests
from openai import OpenAI
from openai.types.chat.chat_completion_content_part_param import ChatCompletionContentPartParam
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

# from python_modules.manipulation.data_types.images import Image
# from python_modules.manipulation.envs.chat_env.hmi import Hmi
# from python_modules.manipulation.platforms.platform import Platform
# from python_modules.manipulation.policies.multi_policy import Behavior
# from python_modules.manipulation.sensors.cameras.camera import Camera
# from python_modules.manipulation.sensors.pedals.pedal import Pedal
# from python_modules.manipulation.utils.audio_utils import AudioPlayer, AudioRecorder
from audio import AudioPlayer, AudioRecorder

GLASS_SOUND = "python_modules/manipulation/assets/sounds/glass.wav"
VOICE_CLONE_URL = "https://api.openai.com/v1/audio/synthesize"
VOICE_CLONE_HEADERS = {
    "Authorization": "Bearer sk-proj-FW1HvpkuoqsuuVnvm7FTT3BlbkFJOsOE2kux5mP5nkW89jRy" # mine
}

ROOT = "/Users/alonrot/artistic/hablaconmigo/aws-elastic-beanstalk-express-js-sample"

logger = logging.getLogger(__name__)

class ChatAgent:
    def __init__(
        self,
        # *,
        # platform: Platform,
        # camera: Optional[Camera[npt.NDArray[np.uint8]]],
        audio: AudioPlayer,
        # pedal: Pedal,
        # behavior_policy: str,
        # text_prompt: str,
        # vision_prompt: str,
        # use_vision: bool = False,
        # verbalize_commands: bool = True,
        openai_api_key: str = "",
        # gpt_responses: Optional[list[dict[str, str]]] = None,
    ) -> None:
        openai.api_key = openai_api_key
        os.environ["OPENAI_API_KEY"] = openai.api_key

        # self._platform = platform
        # self._hmi = Hmi()

        self._gpt_responses = None
        if self._gpt_responses is None:
            # Define robot prompts.
            # behavior_configs = [
            #     hydra.compose(behavior_config).behaviors
            #     for behavior_config in hydra.compose(behavior_policy).policy.behaviors
            # ]
            # self._behaviors = {
            #     config.name: Behavior(name=config.name, description=config.description, policy=None)
            #     for config in behavior_configs
            # }
            # behavior_descriptions = ", ".join(
            #     f"{behavior.name} ({behavior.description})" for behavior in self._behaviors.values()
            # )

            # Initialize the OpenAI API client.
            self._oai_client = OpenAI()
            logger.info("Created OpenAI client.")
            # self.verbalize_commands = verbalize_commands


            # Create audio recorder to listen to speech.
            logger.info("Connecting to microphone...")
            self._recorder = AudioRecorder(channels=1)

            logger.info("Connecting to OpenAI API...")
            if self._test_service():
                logger.info("OpenAI API service is up.")
            else:
                # self._hmi.error()
                raise RuntimeError("OpenAI API service is down.")

            # self._chat_dir = pathlib.Path(ROOT+"/chat_gpt_audio/messages") / datetime.now().strftime(
            self._chat_dir = pathlib.Path("chat_gpt_audio/messages") / datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
            self._chat_dir.mkdir(parents=True)
            self._audio_files = []

            self.reset()
        else:
            self._pedal = pedal
            self._idx_response = 0

        # Create audio player to play responses.
        logger.info("Connecting to speaker...")
        self._audio = audio

    @property
    def audio(self) -> AudioPlayer:
        return self._audio

    # @property
    # def camera(self) -> Optional[Camera[npt.NDArray[np.uint8]]]:
    #     return self._camera

    # @property
    # def hmi(self) -> Hmi:
    #     return self._hmi

    @property
    def oai_client(self) -> OpenAI:
        return self._oai_client

    # @property
    # def pedal(self) -> Pedal:
    #     return self._pedal

    @property
    def recorder(self) -> AudioRecorder:
        return self._recorder

    def close(self) -> None:
        self.audio.close()
        self.hmi.close()
        if self._gpt_responses is None:
            self.recorder.close()

    def _test_service(self) -> bool:
        self.oai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.'",
                },
                {
                    "role": "user",
                    "content": "What is 1+1?.",
                },
            ],
        )
        return True

    def reset(self) -> None:
        """Resets conversation history."""
        logger.info("Resetting agent conversation history.")
        # import pdb; pdb.set_trace()

        # context = "Eres un ser querido que acaba de fallecer. En concreto, eres mi padre. Quiero que hables conmig de manera natural, como si estuvieras vivo y me digas que me quieres muchísimo y que me deseas que sea feliz en la vida."
        context = "Eres mi madre. Eres bibliotecaria y te encanta recomendar libros. Tu comida favorita es la piña. Vives en Villanueva de los Infantes, en España, un pueblo en Castill-La Mancha. Estás deseando que vaya a visitarte."

        if self._gpt_responses is not None:
            self._idx_response = 0
        else:
            self._messages: list[ChatCompletionMessageParam] = [
                # {"role": "system", "content": self._system_prompt}
                {"role": "system", "content": context}
            ]

    def chat_text(self, message: str) -> str:
        # Add user message to history
        self._messages.append({"role": "user", "content": message})

        # Send the messages to the OpenAI API
        logger.info("communicating with OpenAI API...")
        completion = self.oai_client.chat.completions.create(
            model="gpt-4", messages=self._messages, seed=1234
        )

        # Extract the response
        response = completion.choices[0].message
        if response.content is None:
            raise RuntimeError("OpenAI API returned an empty response")

        # Add the assistant's response to the history
        self._messages.append({"role": "assistant", "content": response.content})

        return response.content

    def speech_to_text(self, mp3_file: pathlib.Path | str) -> str:
        # Convert speech to text
        with open(mp3_file, "rb") as audio_file:
            transcript = self.oai_client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="text"
            )
            assert isinstance(transcript, str)
            transcript = transcript.strip()
            logger.info(f"I heard: {transcript}")
        return transcript

    def text_to_speech(
        self, response_text: str, voice: Literal["alloy", "fable", "jared"] = "jared"
    ) -> None:
        # mp3_path = self._chat_dir / f"{len(self._audio_files)}_gpt.mp3"
        # mp3_path = ROOT+"/chat_gpt_audio/mama/merged_audio.mp3"
        # mp3_path_save = ROOT+"/chat_gpt_audio/mama/merged_audio_response.mp3"
        mp3_path = "chat_gpt_audio/mama/merged_audio.mp3"
        mp3_path_save = "chat_gpt_audio/mama/merged_audio_response.mp3"

        # response_text = "Hola, os envío recuerdos desde aquí, desde los Estados Unidos. Y nada, un besooo, adióooos."
        data = {
            "model": "tts-1-hd",
            "text": response_text,
            "speed": "0.95",
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


    def chat(self) -> Optional[list[str]]:
        # self.audio.play(GLASS_SOUND)
        # self._hmi.ready()
        logger.info("Ready")

        # Block to get a recording (purple light while recording).
        # logger.info(f"Recorder recording: {self._recorder.recording}")
        logger.info(f"Recorder recording ...")
        maybe_recorded_file = self._recorder.wait_for_recorded_file(
            # on_record_callback=self._hmi.listening,
            # wav_path=self._chat_dir / f"{len(self._audio_files)}_user.mp3",
            wav_path=self._chat_dir / f"{len(self._audio_files)}_user.mp3",
        )
        print("maybe_recorded_file: ", maybe_recorded_file)
        # import pdb;pdb.set_trace()
        if maybe_recorded_file is None:
            return
        recorded_file = maybe_recorded_file
        self._audio_files.append(recorded_file)

        # self._hmi.thinking()
        logger.info("Thinking")

        # Convert speech to text
        transcript = self.speech_to_text(recorded_file)
        print("transcript: ", transcript)

        # Get response from the chatbot
        # if self._use_vision:
        #     response_text = self.chat_vision_text(f"USER: {transcript}")
        # else:
        response_text = self.chat_text(f"USER: {transcript}")
        if response_text is None:
            return
        logger.warn(response_text)

        response = response_text.replace("ANSWER:", "")

        # Verbalize response.
        # self.hmi.speaking(0, 0)
        print("Speaking...")
        self.text_to_speech(response)
        return None


