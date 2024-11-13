# ai_agent/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json
import base64
import os
import asyncio
import websockets
import openai
from django.conf import settings

openai.api_key = os.getenv("OPENAI_API_KEY")

DEEGRAM_STT_WEBSOCKET_URL = (
    "wss://api.deepgram.com/v1/listen?"
    "model=nova-2-phonecall&language=en&encoding=mulaw&sample_rate=8000&channels=1&"
    "smart_format=true&interim_results=true&utterance_end_ms=1000"
)
DEEGRAM_TTS_WEBSOCKET_URL = (
    "wss://api.deepgram.com/v1/speak?encoding=mulaw&sample_rate=8000&container=none"
)
CHARS_TO_CHECK = [".", ",", "!", "?", ";", ":"]


class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("WebSocket connection accepted")
        # Initialize variables
        self.stream_sid = ""
        self.speaking = False
        self.has_seen_media = False
        self.is_finals = []
        self.queue = asyncio.Queue()
        self.deepgram_stt = None
        self.deepgram_tts = None
        # Start tasks
        asyncio.create_task(self.connect_deepgram_stt())
        asyncio.create_task(self.connect_deepgram_tts())
        asyncio.create_task(self.process_queue())

    async def disconnect(self, close_code):
        print("WebSocket connection closed")
        await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            await self.queue.put(text_data)

    async def connect_deepgram_stt(self):
        headers = {"Authorization": f"Token {os.getenv('DEEPGRAM_API_KEY')}"}
        retry_delay = 5
        while True:
            try:
                self.deepgram_stt = await websockets.connect(
                    DEEGRAM_STT_WEBSOCKET_URL, extra_headers=headers
                )
                asyncio.create_task(self.listen_deepgram_stt())
                break
            except Exception as e:
                print(
                    f"Deepgram STT connection failed: {e}. Retrying in {retry_delay} seconds..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)

    async def connect_deepgram_tts(self):
        headers = {"Authorization": f"Token {os.getenv('DEEPGRAM_API_KEY')}"}
        retry_delay = 5
        while True:
            try:
                self.deepgram_tts = await websockets.connect(
                    DEEGRAM_TTS_WEBSOCKET_URL, extra_headers=headers
                )
                asyncio.create_task(self.listen_deepgram_tts())
                break
            except Exception as e:
                print(
                    f"Deepgram TTS connection failed: {e}. Retrying in {retry_delay} seconds..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)

    async def listen_deepgram_stt(self):
        try:
            async for message in self.deepgram_stt:
                data = json.loads(message)
                message_type = data.get("type")
                if message_type == "Results":
                    await self.handle_deepgram_transcript(data)
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Deepgram STT connection closed: {e}")

    async def listen_deepgram_tts(self):
        try:
            async for message in self.deepgram_tts:
                if self.speaking:
                    if isinstance(message, bytes):
                        payload = base64.b64encode(message).decode()
                        response = {
                            "event": "media",
                            "streamSid": self.stream_sid,
                            "media": {"payload": payload},
                        }
                        await self.send(text_data=json.dumps(response))
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Deepgram TTS connection closed: {e}")

    async def handle_deepgram_transcript(self, data):
        if data.get("is_final"):
            transcript = data["channel"]["alternatives"][0]["transcript"]
            if transcript:
                self.is_finals.append(transcript)
                if data.get("speech_final"):
                    utterance = " ".join(self.is_finals)
                    self.is_finals = []
                    asyncio.create_task(self.prompt_llm(utterance))
        else:
            # Handle interim results if needed
            pass

    async def process_queue(self):
        try:
            while True:
                message = await self.queue.get()
                data = json.loads(message)
                event = data.get("event")
                if event == "connected":
                    pass
                elif event == "start":
                    self.stream_sid = data.get("streamSid", "")
                elif event == "media":
                    if data.get("media", {}).get("track") == "inbound":
                        raw_audio = base64.b64decode(data["media"]["payload"])
                        if self.deepgram_stt and self.deepgram_stt.open:
                            await self.deepgram_stt.send(raw_audio)
                elif event == "close":
                    await self.close()
        except Exception as e:
            print(f"Error processing queue: {e}")

    async def close(self):
        if self.deepgram_stt:
            await self.deepgram_stt.close()
        if self.deepgram_tts:
            await self.deepgram_tts.close()
        await super().close()

    async def prompt_llm(self, prompt):
        self.speaking = True
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "assistant",
                        "content": """
You are the outbound voice assistant for Army of Me.

[Your detailed system prompt here]
                        """,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                stream=True,
            )

            async for chunk in response:
                if self.speaking:
                    if "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        chunk_message = delta.get("content", "")
                        if chunk_message:
                            if self.deepgram_tts and self.deepgram_tts.open:
                                await self.deepgram_tts.send(
                                    json.dumps({"type": "Speak", "text": chunk_message})
                                )
            if self.deepgram_tts and self.deepgram_tts.open:
                await self.deepgram_tts.send(json.dumps({"type": "Flush"}))
        except Exception as e:
            print(f"Error prompting LLM: {e}")
            self.speaking = False
