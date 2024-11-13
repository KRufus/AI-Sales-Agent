import asyncio
import base64
import json
import logging
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
# from .models import Call, Transcription
from twilio.rest import Client
from pydub import AudioSegment
import websockets
from .utils import response_for_gpt, convert_text_to_speech
from twilio.twiml.voice_response import VoiceResponse

logger = logging.getLogger(__name__)


class TwilioDeepgramConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.outbox = asyncio.Queue()
        self.deepgram_ws = None
        logger.info("WebSocket connection accepted.")
        
        # Start the Deepgram connection
        asyncio.create_task(self.deepgram_connect())

    async def disconnect(self, close_code):
        logger.info("WebSocket connection closed.")
        if self.deepgram_ws:
            await self.deepgram_ws.close()

    async def deepgram_connect(self):
        try:
            self.deepgram_ws = await websockets.connect(
                "wss://api.deepgram.com/v1/listen?encoding=mulaw&sample_rate=8000&channels=2&multichannel=true",
                extra_headers={'Authorization': f"Token {settings.DEEPGRAM_API_KEY}"}
            )
            logger.info("Connected to Deepgram WebSocket.")
            asyncio.create_task(self.deepgram_receiver())
            await self.deepgram_sender()
        except Exception as e:
            logger.error(f"Deepgram connection error: {e}")

    async def deepgram_sender(self):
        while True:
            chunk = await self.outbox.get()
            if chunk is None:
                break
            try:
                await self.deepgram_ws.send(chunk)
            except Exception as e:
                logger.error(f"Error sending data to Deepgram: {e}")
                break

        await self.deepgram_ws.send(b'')
        logger.info("Deepgram sender task terminated.")

    async def deepgram_receiver(self):
        try:
            async for message in self.deepgram_ws:
                try:
                    dg_json = json.loads(message)
                    if "results" in dg_json:
                        # Extract transcription result
                        speech_result = dg_json['results']['channels'][0]['alternatives'][0]['transcript']
                        # Process the transcription result
                        await self.handle_customer_response(speech_result)
                except json.JSONDecodeError:
                    logger.warning("Received non-JSON message from Deepgram.")
        except websockets.ConnectionClosed:
            logger.info("Deepgram connection closed.")
        finally:
            await self.close()

    async def handle_customer_response(self, speech_result):
        """
        Send customer input to GPT-3.5, convert the response to TTS, and play back to the customer.
        """
        gpt_response = await response_for_gpt(speech_result)
        print(gpt_response, "gpt_response")
        tts_audio_url = await convert_text_to_speech({"text": gpt_response}, prefix="ai")
        print(tts_audio_url, "tts_audio_url")

        # Send back the generated TTS response URL to Twilio to play for the customer
        await self.send_to_twilio(tts_audio_url)

    async def send_to_twilio(self, audio_url):
        """
        Send the TTS audio back to the customer using Twilio's `<Play>` command.
        """
        response = VoiceResponse()
        response.play(audio_url)
        await self.send(text_data=response.to_xml())

