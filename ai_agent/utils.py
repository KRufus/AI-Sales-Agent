# sales-backend/assistant/utils.py

import requests
import os
import logging
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def generate_voice(text):
    url = "https://api.elevenlabs.io/v1/text-to-speech/Xb7hH8MSUJpSbSDYk0k2"  # Replace with your actual endpoint

    # Use environment variable for the API key for security reasons
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("ELEVENLABS_API_KEY not found in environment variables.")
        raise EnvironmentError("ELEVENLABS_API_KEY not set.")

    headers = {
        'xi-api-key': api_key,
        'Content-Type': 'application/json',
    }

    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.1,
            "similarity_boost": 0.3,
            "style": 0.2,
            "optimize_streaming_latency": "0",
            "output_format": "mp3_22050_32"
        }
    }

    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=data)

        # Log response status and headers for debugging
        logger.info(f"ElevenLabs Response Status Code: {response.status_code}")
        logger.info(f"ElevenLabs Response Headers: {response.headers}")

        # Check for success
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if content_type.startswith('audio/'):
                # Save the audio content to a file
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                file_name = f"output_audio_{timestamp}.mp3"
                file_path = os.path.join('audio_files', file_name)  # Ensure 'audio_files' directory exists

                # Use Django's default storage system
                saved_path = default_storage.save(file_path, ContentFile(response.content))
                logger.info(f"Audio file saved to: {saved_path}")
                return settings.MEDIA_URL + saved_path  # Return the URL to access the file
            elif content_type == 'application/json':
                try:
                    json_response = response.json()
                    audio_url = json_response.get('url')  # Adjust based on actual API response
                    logger.info(f"Audio URL received: {audio_url}")
                    return audio_url
                except ValueError:
                    logger.error("Failed to parse JSON response from ElevenLabs.")
                    raise Exception("Failed to parse JSON response.")
            else:
                logger.error(f"Unexpected content type: {content_type}")
                raise Exception(f"Unexpected content type: {content_type}")
        else:
            logger.error(f"Error: Received {response.status_code} status code from ElevenLabs.")
            logger.error(f"Response Text: {response.text}")
            raise Exception(f"Error: {response.status_code}, {response.text}")
    except requests.RequestException as e:
        logger.exception("Request to ElevenLabs API failed.")
        raise Exception(f"Request to ElevenLabs API failed: {str(e)}")
