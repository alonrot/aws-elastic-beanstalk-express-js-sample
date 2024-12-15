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

logger = logging.getLogger(__name__)


from chat import ChatAgent

# Use this code snippet in your app.
# If you need more information about configurations
# or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developer/language/python/

import boto3
from botocore.exceptions import ClientError


def get_secret():

    secret_name = "chatgpt"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']

    return secret



if __name__ == "__main__":


    web = False
    if web:
        openai_api_key = get_secret()
    else:
        # Read from local file
        with open("my_api", "r") as f:
            openai_api_key = f.read



    audio = AudioPlayer(device='MacBook Pro Speakers')
    chat_agent = ChatAgent(audio=audio, openai_api_key=openai_api_key)

    while True:
        print("ask a question NOWWW!!")
        chat_agent.chat()
        print("Iteration finished. Sleeping for 5 seconds")
        time.sleep(5.0)

