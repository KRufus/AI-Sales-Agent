import os
import time
import wave
import boto3
import random
import string
# import requests
import logging
from deepgram import Deepgram
from datetime import datetime
from deepgram import DeepgramClient, SpeakWebSocketEvents, SpeakWSOptions
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import aiohttp
import asyncio
from deepgram import (
    DeepgramClient,
    ClientOptionsFromEnv,
    SpeakOptions,
)

logger = logging.getLogger(__name__)
AUDIO_FILE = "output.wav"
DEEPGRAM_API_KEY=os.getenv("DEEPGRAM_API_KEY")
dg_client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))



async def generate_voice(text):
    print("\n\n ______ generate_voice function was triggered")
    try:
    
        dg_connection = dg_client.speak.websocket.v("1")
        
        file_complete = asyncio.Event()

        # Callback functions for WebSocket events
        def on_open(self, open, **kwargs):
            print(f"WebSocket opened:_____ {open}")

        # def on_binary_data(self, data, **kwargs):
        #     print("Received binary data _____")
        #     # Save streamed binary audio to the WAV file
        #     with default_storage.open(audio_file_path, "ab") as f:
        #         f.write(data)
        #         f.flush()
                
        # def on_binary_data(self, data, **kwargs):
        #     print("Received binary data _____")
        #     with default_storage.open(audio_file_path, "ab") as f:
        #         f.write(data)

        # def on_close(self, close, **kwargs):
        #     print(f"WebSocket closed:_____ {close}")
            
        def on_close(self, close, **kwargs):
            print(f"WebSocket closed:_____ {close}")
            file_complete.set()

        # Set the event handlers
        # dg_connection.on(SpeakWebSocketEvents.Open, on_open)
        # dg_connection.on(SpeakWebSocketEvents.AudioData, on_binary_data)
        # dg_connection.on(SpeakWebSocketEvents.Close, on_close)

        # Generate a generic WAV header for the audio file
        # header = wave.open(AUDIO_FILE, "wb")
        # header.setnchannels(1)  # Mono audio
        # header.setsampwidth(2)  # 16-bit audio
        # header.setframerate(16000)  # 16000 Hz sample rate
        # # header.close()
        
        # header = wave.open(audio_file_path, "wb")
        # header.setnchannels(1)  # Mono audio
        # header.setsampwidth(2)  # 16-bit audio
        # header.setframerate(16000)  # 16000 Hz sample rate
        # header.close()

        # WebSocket connection options
        # options = SpeakWSOptions(
        #     model="aura-asteria-en",
        #     encoding="linear16",
        #     sample_rate=16000
        # )

        # if dg_connection.start(options) is False:
        #     print("Failed to start connection")
        #     return
        
        # if  dg_connection.start(options) is False:
        #     print("Failed to start connection")
        #     return

        
        # dg_connection.send_text(text)
        # dg_connection.flush()
        
        dg_connection.send_text(text)
        dg_connection.flush()

        # Allow time for processing and streaming the audio data
        # time.sleep(10)
        
        file_complete.wait()

        # dg_connection.finish()
        # logger.info(f"Audio file saved to: {AUDIO_FILE}")
        
        # await dg_connection.finish()
        # logger.info(f"Audio file saved to: {audio_file_path}")
        
        try:
            dg_connection.finish()
        except Exception as e:
            print(f"Failed to close connection: {e}")
            raise
        
        # logger.info(f"Audio file saved to: {audio_file_path}")

        
        
        # logger.info(f"Audio file uploaded to S3: {s3_file_url}")
        
        return ""

        # return settings.MEDIA_URL + AUDIO_FILE

    except Exception as e:
        logger.error(f"Deepgram API request failed: {e}")
        raise Exception(f"Deepgram API request failed: {e}")
    
    
    

from minio import Minio
from minio.error import S3Error
import mimetypes
from minio.commonconfig import REPLACE, CopySource
import datetime


minio_client = Minio(
    "localhost:9000",
    access_key="ROOTUSER",
    secret_key="CHANGEME123",
    secure=False
)

bucket_name = "aisalesagent"
filename = "test.mp3"
minio_path = "audio/" + filename  

SPEAK_TEXT = {"text":f"Hello Amul, this is Ginie from Army of Me. I hope you're doing well today! We provide a range of accounting and financial services, including bookkeeping, tax preparation, payroll processing, and more. Is there a particular service you are interested in, or would you like an overview of our offerings? "}

async def convert_text_to_speech():
    print("minio_client", "minio_client")
    try:
        options = SpeakOptions(
            model="aura-asteria-en",
        )
        
        print(options, "options")

        response = await dg_client.speak.asyncrest.v("1").save(
            filename, SPEAK_TEXT, options
        )

        print(response.to_json(indent=4))

        found = minio_client.bucket_exists(bucket_name)
        
        if not found:
            minio_client.make_bucket(bucket_name)
        
        mime_type, _ = mimetypes.guess_type(filename)
        
        if not mime_type:
            mime_type = "application/octet-stream"
        
        minio_client.fput_object(
            bucket_name, 
            minio_path, 
            filename, 
            content_type=mime_type,
            metadata={
                "Cache-Control": "max-age=3600, public",
                "Last-Modified": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
                "ETag": "1234567890"
            }
        )
        
        
        print(f"File '{filename}' uploaded with MIME type '{mime_type}'.")
        
        public_url = f"{settings.EXTERNAL_NGROK_URL}{bucket_name}/{minio_path}"
        return public_url

    except S3Error as e:
        print(f"S3Error: {e}")
    except Exception as e:
        print(f"Exception: {e}")



# asyncio.run(convert_text_to_speech())