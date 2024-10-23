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

logger = logging.getLogger(__name__)

AUDIO_FILE = "output.wav"

# Initialize Deepgram client
# dg_client = Deepgram(os.getenv("DEEPGRAM_API_KEY"))
dg_client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

# # Asynchronous function for generating voice using Deepgram ####################################################
# async def generate_voice(text):
#     print("\n\n ______ generate_voice function was triggered")
#     try:
#         # # Make a request to the Deepgram TTS API
#         # response = dg_client.speak({
#         #     "text": text,
#         #     "voice": "en-US",
#         #     "model": "aura-helios-en"
#         #     # "model": "aura-hera-en"
#         # })
        
#         # print("\n\n\n")
#         # print(" response _____ ", response)

#         # # Log and save the audio content to a file
#         # if response.status == 200:
#         #     timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#         #     file_name = f"output_audio_{timestamp}.mp3"
#         #     file_path = os.path.join('audio_files', file_name)

#         #     # Use Django's storage system to save audio
#         #     saved_path = default_storage.save(file_path, ContentFile(response['audio']))
#         #     logger.info(f"Audio file saved to: {saved_path}")
#         #     return settings.MEDIA_URL + saved_path  # Return the URL to access the file

#         # else:
#         #     logger.error(f"Deepgram TTS Error: {response.status}")
#         #     raise Exception(f"Deepgram TTS Error: {response.status}")



#         # Set up streaming URL
#         # url = "https://api.deepgram.com/v1/speak/stream"
#         url = "https://api.deepgram.com/v1/speak"

#         # Prepare headers and request body
#         headers = {
#             "Authorization": f"Token {os.getenv('DEEPGRAM_API_KEY')}",
#             "Content-Type": "application/json"
#         }
#         data = {
#             "text": text,
#             "voice": "en-US",
#             "model": "aura-helios-en",
#             "encoding": "mp3"
#         }

#         # Set up async HTTP session for streaming
#         async with aiohttp.ClientSession() as session:
#             async with session.post(url, headers=headers, json=data) as response:
#                 if response.status == 200:
#                     timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#                     file_name = f"output_audio_{timestamp}.mp3"
#                     file_path = os.path.join('audio_files', file_name)

#                     # Stream the audio content and save it to a file
#                     with default_storage.open(file_path, 'wb') as f:
#                         async for chunk in response.content.iter_chunked(1024):
#                             f.write(chunk)

#                     logger.info(f"Audio file saved to: {file_path}")
#                     return settings.MEDIA_URL + file_path  # Return the URL to access the file
#                 else:
#                     logger.error(f"Deepgram TTS Error: {response.status}")
#                     raise Exception(f"Deepgram TTS Error: {response.status}")

#     except Exception as e:
#         logger.error(f"Deepgram API request failed: {e}")
#         raise Exception(f"Deepgram API request failed: {e}")


def generate_unique_filename(extension="wav"):
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"audio_{random_string}.{extension}"

def upload_to_s3(file_path, file_name):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    
    region = settings.AWS_REGION
    
    s3.upload_file(file_path, bucket_name, file_name)

    file_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/models/{file_name}"
    return file_url



async def generate_voice(text):
    print("\n\n ______ generate_voice function was triggered")
    try:
        
        unique_audio_file_name = generate_unique_filename()
        audio_file_path = os.path.join(settings.MEDIA_ROOT, unique_audio_file_name)
        
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
                
        def on_binary_data(self, data, **kwargs):
            print("Received binary data _____")
            with default_storage.open(audio_file_path, "ab") as f:
                f.write(data)

        # def on_close(self, close, **kwargs):
        #     print(f"WebSocket closed:_____ {close}")
            
        def on_close(self, close, **kwargs):
            print(f"WebSocket closed:_____ {close}")
            file_complete.set()

        # Set the event handlers
        dg_connection.on(SpeakWebSocketEvents.Open, on_open)
        dg_connection.on(SpeakWebSocketEvents.AudioData, on_binary_data)
        dg_connection.on(SpeakWebSocketEvents.Close, on_close)

        # Generate a generic WAV header for the audio file
        # header = wave.open(AUDIO_FILE, "wb")
        # header.setnchannels(1)  # Mono audio
        # header.setsampwidth(2)  # 16-bit audio
        # header.setframerate(16000)  # 16000 Hz sample rate
        # header.close()
        
        header = wave.open(audio_file_path, "wb")
        header.setnchannels(1)  # Mono audio
        header.setsampwidth(2)  # 16-bit audio
        header.setframerate(16000)  # 16000 Hz sample rate
        header.close()

        # WebSocket connection options
        options = SpeakWSOptions(
            model="aura-asteria-en",
            encoding="linear16",
            sample_rate=16000
        )

        # if dg_connection.start(options) is False:
        #     print("Failed to start connection")
        #     return
        
        if  dg_connection.start(options) is False:
            print("Failed to start connection")
            return

        
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
        
        logger.info(f"Audio file saved to: {audio_file_path}")
        
        # s3_file_url = upload_to_s3(audio_file_path, unique_audio_file_name)
        
        try:
            s3_file_url = upload_to_s3(audio_file_path, unique_audio_file_name)
        except Exception as e:
            logger.error(f"Failed to upload audio file to S3: {e}")
            raise
        
        
        logger.info(f"Audio file uploaded to S3: {s3_file_url}")
        
        return s3_file_url

        # return settings.MEDIA_URL + AUDIO_FILE

    except Exception as e:
        logger.error(f"Deepgram API request failed: {e}")
        raise Exception(f"Deepgram API request failed: {e}")
    
    
    
# async def test_generate_voice():
#     text = (
#         "Hello, this is Ginie from Army of Me. I hope you're doing well today! "
#         "We provide a range of accounting and financial services, including bookkeeping, tax preparation, payroll processing, and more. "
#         "Is there a particular service you are interested in, or would you like an overview of our offerings?"
#     )
#     result = await generate_voice(text)
#     print(result)

# # Run the test function
# asyncio.run(test_generate_voice())
