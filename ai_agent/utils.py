import os
import time
import wave
import requests
import logging
from deepgram import Deepgram
from datetime import datetime
from deepgram import DeepgramClient, SpeakWebSocketEvents, SpeakWSOptions
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import aiohttp

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





async def generate_voice(text):
    print("\n\n ______ generate_voice function was triggered")
    try:
        # Create a websocket connection to Deepgram
        dg_connection = dg_client.speak.websocket.v("1")

        # Callback functions for WebSocket events
        def on_open(self, open, **kwargs):
            print(f"WebSocket opened:_____ {open}")

        def on_binary_data(self, data, **kwargs):
            print("Received binary data _____")
            # Save streamed binary audio to the WAV file
            with default_storage.open(AUDIO_FILE, "ab") as f:
                f.write(data)
                f.flush()

        def on_close(self, close, **kwargs):
            print(f"WebSocket closed:_____ {close}")

        # Set the event handlers
        dg_connection.on(SpeakWebSocketEvents.Open, on_open)
        dg_connection.on(SpeakWebSocketEvents.AudioData, on_binary_data)
        dg_connection.on(SpeakWebSocketEvents.Close, on_close)

        # Generate a generic WAV header for the audio file
        header = wave.open(AUDIO_FILE, "wb")
        header.setnchannels(1)  # Mono audio
        header.setsampwidth(2)  # 16-bit audio
        header.setframerate(16000)  # 16000 Hz sample rate
        header.close()

        # WebSocket connection options
        options = SpeakWSOptions(
            model="aura-asteria-en",
            encoding="linear16",
            sample_rate=48000
        )

        if dg_connection.start(options) is False:
            print("Failed to start connection")
            return

        # Send the text to Deepgram for TTS conversion
        dg_connection.send_text(text)
        dg_connection.flush()

        # Allow time for processing and streaming the audio data
        time.sleep(5)

        dg_connection.finish()
        logger.info(f"Audio file saved to: {AUDIO_FILE}")
        return settings.MEDIA_URL + AUDIO_FILE

    except Exception as e:
        logger.error(f"Deepgram API request failed: {e}")
        raise Exception(f"Deepgram API request failed: {e}")
