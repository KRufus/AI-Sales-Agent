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
import websockets
import requests
import json
import aiohttp
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
from_phone_number = os.getenv("TWILIO_PHONE_NUMBER")


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


async def handle_conversation_loop(recording_url, call_sid):
    if not recording_url:
        print("Recording URL is None, exiting loop")
        return
    
    uri = f"wss://api.deepgram.com/v1/listen?model=general&language=en-US"
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}

    try:
        print("Attempting to connect to Deepgram WebSocket...")
        async with websockets.connect(uri, extra_headers=headers) as websocket:
            print("Connected to Deepgram WebSocket.")
            
            keep_alive_task = asyncio.create_task(send_keep_alive(websocket))

            async with aiohttp.ClientSession() as session:
                async with session.get(recording_url) as audio_response:
                    print("Streaming audio data to Deepgram WebSocket...")
                    async for chunk in audio_response.content.iter_chunked(1024):
                        await websocket.send(chunk)
                        print("Sent audio chunk to WebSocket.")
                        
                        
                        
            await websocket.send(json.dumps({"type": "CloseStream"}))
            print("Sent CloseStream message.")

            # Cancel the keep_alive_task
            keep_alive_task.cancel()


            print("Finished sending audio, waiting for Deepgram responses...")
            async for message in websocket:
                data = json.loads(message)
                print("Received message from WebSocket:", data)

                if data['type'] == 'Metadata':
                    print("Received metadata. Ready to process audio.")
                elif 'channel' in data:
                    # Process transcription results
                    transcript = data["channel"]["alternatives"][0]["transcript"]
                    print("Transcription received:", transcript)
                else:
                    print("Unexpected message type:", data['type'])

                        # Respond to the user through Twilio
                await say_to_user(transcript, call_sid)

    except Exception as e:
        print(f"Error in WebSocket connection or processing: {e}")
        
        
        
async def send_keep_alive(websocket):
    while True:
        try:
            await asyncio.sleep(8)  # Send KeepAlive every 8 seconds
            await websocket.send(json.dumps({"type": "KeepAlive"}))
            print("Sent KeepAlive message.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error sending KeepAlive: {e}")
            break
                    

async def say_to_user(text, call_sid):
    # global call_sid
    if not call_sid:
        print("No call SID found.")
        return

    # Create new TwiML response to say the new text
    response = VoiceResponse()
    response.say(text)

    # Update the ongoing call with the new TwiML response
    twilio_client.calls(call_sid).update(twiml=response)
    print("Response sent to user:", text)