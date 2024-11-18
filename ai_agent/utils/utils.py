import os
import time

import logging
from deepgram import Deepgram
from datetime import datetime
from deepgram import DeepgramClient
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import asyncio
from deepgram import (
    DeepgramClient,
    SpeakOptions,
)
from minio.error import S3Error
import mimetypes
import datetime
import websockets
import requests
import json
import aiohttp
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import datetime
import uuid
import traceback
from .minio import minio_client, bucket_name, minio_base_path
import openai
import time
from minio import S3Error

twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
from_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
logger = logging.getLogger(__name__)

dg_client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)

async def convert_text_to_speech(speak_text, prefix="ai"):
    print(f"Starting convert_text_to_speech with text: {speak_text}")
    start_time = time.time()
    try:
        # Generate unique filename
        filename = f"{prefix}_{uuid.uuid4().hex}.mp3"
        minio_path = f"{minio_base_path}{filename}"
        print(f"Generated filename: {filename}")

        # Set text-to-speech options
        options = SpeakOptions(model="aura-asteria-en")

        # Measure time taken for text-to-speech conversion
        tts_start = time.time()
        try:
            response = await dg_client.speak.asyncrest.v("1").save(filename, speak_text, options)
        except Exception as e:
            print("Error during text-to-speech conversion:", e)
            traceback.print_exc()
            return None
        tts_end = time.time()
        print(f"Text-to-speech conversion took {tts_end - tts_start:.2f} seconds")

        # Check and create MinIO bucket if necessary
        bucket_start = time.time()
        try:
            found = minio_client.bucket_exists(bucket_name)
            if not found:
                minio_client.make_bucket(bucket_name)
                print(f"Bucket '{bucket_name}' created")
        except S3Error as e:
            print(f"S3Error while checking/creating bucket: {e}")
            traceback.print_exc()
            return None
        except Exception as e:
            print("Error in bucket check/create operation:", e)
            traceback.print_exc()
            return None
        bucket_end = time.time()
        print(f"Bucket check/creation took {bucket_end - bucket_start:.2f} seconds")

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        print(f"Determined MIME type: {mime_type}")

        # Upload file to MinIO
        upload_start = time.time()
        try:
            minio_client.fput_object(
                bucket_name,
                minio_path,
                filename,
                content_type=mime_type,
                metadata={
                    "Cache-Control": "max-age=3600, public",
                    "Last-Modified": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "ETag": str(uuid.uuid4())
                }
            )
        except S3Error as e:
            print(f"S3Error during file upload to MinIO: {e}")
            traceback.print_exc()
            return None
        except Exception as e:
            print("Error during file upload to MinIO:", e)
            traceback.print_exc()
            return None
        upload_end = time.time()
        print(f"File upload took {upload_end - upload_start:.2f} seconds")

        public_url = f"https://ai-ds-api.armyof.me/{bucket_name}/{minio_path}"
        print(f"File '{filename}' uploaded and available at {public_url}")

        total_time = time.time() - start_time
        print(f"Total processing time: {total_time:.2f} seconds")

        return public_url

    except Exception as e:
        print("An unexpected error occurred:", e)
        traceback.print_exc()
        return None


# async def convert_text_to_speech(speak_text, prefix="ai"):
#     print(speak_text, "minio_client")
#     try:
       
#         filename = f"{prefix}_{uuid.uuid4().hex}.mp3"
#         minio_path = f"{minio_base_path}{filename}"
        
#         # print(filename, minio_path, "filename, minio_path")
        
#         options = SpeakOptions(model="aura-asteria-en")

#         try:
#             response = await dg_client.speak.asyncrest.v("1").save(filename, speak_text, options)
#         except Exception as e:
#             print("Error during text-to-speech conversion:", e)
#             traceback.print_exc()
#             return None

#         try:
#             found = minio_client.bucket_exists(bucket_name)
#             if not found:
#                 minio_client.make_bucket(bucket_name)
#         except S3Error as e:
#             print(f"S3Error while checking/creating bucket: {e}")
#             traceback.print_exc()
#             return None
#         except Exception as e:
#             print("Error in bucket check/create operation:", e)
#             traceback.print_exc()
#             return None

#         # Determine MIME type
#         mime_type, _ = mimetypes.guess_type(filename)
#         if not mime_type:
#             mime_type = "application/octet-stream"

#         # print(minio_client, "minio_client")

#         try:
#             minio_client.fput_object(
#                 bucket_name, 
#                 minio_path, 
#                 filename, 
#                 content_type=mime_type,
#                 metadata={
#                     "Cache-Control": "max-age=3600, public",
#                     "Last-Modified": datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
#                     "ETag": str(uuid.uuid4())
#                 }
#             )
#         except S3Error as e:
#             print(f"S3Error during file upload to MinIO: {e}")
#             traceback.print_exc()
#             return None
#         except Exception as e:
#             print("Error during file upload to MinIO:", e)
#             traceback.print_exc()
#             return None

#         public_url = f"https://ai-ds-api.armyof.me/{bucket_name}/{minio_path}"
#         print(f"File '{filename}' uploaded with MIME type '{mime_type}' and available at {public_url}")

#         return public_url

#     except Exception as e:
#         print("An unexpected error occurred:", e)
#         traceback.print_exc()
#         return None


async def response_for_gpt(speechResult):
    print("Function called: response_for_gpt")
    start_time = time.time()
    max_chars = 500
    max_tokens = 150  # Reduced max_tokens to speed up response
    print(f"Input speechResult: {speechResult}")

    try:
        # Using 'n' parameter to limit the number of completions to 1
        # and setting 'temperature' to 0.7 for a balance between speed and creativity
        ai_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            max_tokens=max_tokens,
            n=1,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant."
                        "Please provide concise and brief answers, no longer than 500 words. "
                        "Avoid unnecessary details."
                    )
                },
                {"role": "user", "content": speechResult}
            ]
        ).choices[0].message['content'].strip()

        print(f"Raw ai_response: {ai_response}")

        if len(ai_response) > max_chars:
            ai_response = ai_response[:max_chars]
            print("Truncated ai_response to max_chars")

        end_time = time.time()
        print(f"Response generated in {end_time - start_time:.2f} seconds")

        return ai_response

    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        return "Sorry, an error occurred while processing your request."