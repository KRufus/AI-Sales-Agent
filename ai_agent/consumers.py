# ai_agent/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json
import base64
import os
import asyncio
import websockets
import openai
import time

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
        # Start tasks
        asyncio.create_task(self.connect_deepgram_stt())
        asyncio.create_task(self.process_queue())
        # Timing variables
        self.stt_start_time = None
        self.tts_start_time = None
        # Interruption flag
        self.interrupt_speech = False
        # Event to signal TTS completion
        self.tts_finished = asyncio.Event()
        # Task references
        self.tts_task = None
        self.openai_task = None  # Task reference for OpenAI API call

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

    async def listen_deepgram_stt(self):
        try:
            async for message in self.deepgram_stt:
                data = json.loads(message)
                message_type = data.get("type")
                if message_type == "Results":
                    await self.handle_deepgram_transcript(data)
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Deepgram STT connection closed: {e}")

    async def handle_deepgram_transcript(self, data):
        if data.get("is_final"):
            transcript = data["channel"]["alternatives"][0]["transcript"]
            if transcript:
                # Record STT start time if not already set
                if not self.stt_start_time:
                    self.stt_start_time = time.time()
                self.is_finals.append(transcript)
                if data.get("speech_final"):
                    utterance = " ".join(self.is_finals)
                    self.is_finals = []
                    # Print the received transcript
                    print(f"Received transcript: {utterance}")
                    # Measure STT time
                    if self.stt_start_time:
                        stt_end_time = time.time()
                        stt_total_time = stt_end_time - self.stt_start_time
                        print(f"STT processing time: {stt_total_time:.2f} seconds")
                        self.stt_start_time = None  # Reset for next utterance
                    # If user speaks while AI is speaking, interrupt AI speech
                    if self.speaking:
                        print(
                            "User started speaking while AI is speaking. Interrupting AI speech."
                        )
                        self.interrupt_speech = True  # Set the interruption flag
                        # Send clear message to stop playback on Twilio
                        await self.send_clear_message()
                        # Cancel OpenAI task if running
                        if self.openai_task and not self.openai_task.done():
                            self.openai_task.cancel()
                        # Cancel TTS task and close TTS WebSocket
                        if self.tts_task:
                            self.tts_task.cancel()
                            self.tts_task = None
                    # Start processing new user input
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
        await super().close()

    async def prompt_llm(self, prompt):
        # If AI speech was interrupted previously, reset the flag and state
        if self.interrupt_speech:
            self.interrupt_speech = False
            self.speaking = False
        self.speaking = True
        try:
            # Start timing OpenAI response
            openai_start_time = time.time()
            # Create an asyncio task for the OpenAI API call
            self.openai_task = asyncio.create_task(self.generate_ai_response(prompt))

            # Wait for the OpenAI task to complete or be canceled
            await self.openai_task

        except asyncio.CancelledError:
            print("prompt_llm task was cancelled.")
        except Exception as e:
            print(f"Error in prompt_llm: {e}")
        finally:
            self.speaking = False

    async def generate_ai_response(self, prompt):
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

            # Prepare to collect the full response
            full_response = ""

            # Create a new TTS connection
            tts_headers = {"Authorization": f"Token {os.getenv('DEEPGRAM_API_KEY')}"}
            tts_ws = await websockets.connect(
                DEEGRAM_TTS_WEBSOCKET_URL, extra_headers=tts_headers
            )

            # Start listening to TTS messages
            self.tts_task = asyncio.create_task(self.listen_deepgram_tts(tts_ws))

            async for chunk in response:
                if self.interrupt_speech:
                    print("AI speech was interrupted by user input.")
                    # Cancel OpenAI API call
                    break
                if "choices" in chunk and len(chunk["choices"]) > 0:
                    delta = chunk["choices"][0].get("delta", {})
                    chunk_message = delta.get("content", "")
                    if chunk_message:
                        # Collect the full response
                        full_response += chunk_message
                        # Print the AI response chunk
                        print(f"AI Response Chunk: {chunk_message}")
                        if tts_ws and tts_ws.open:
                            await tts_ws.send(
                                json.dumps({"type": "Speak", "text": chunk_message})
                            )

            if not self.interrupt_speech and tts_ws and tts_ws.open:
                await tts_ws.send(json.dumps({"type": "Flush"}))
                # Start timing TTS processing
                self.tts_start_time = time.time()
                # Wait for TTS to finish
                await self.tts_finished.wait()
                self.tts_finished.clear()  # Reset the event for next time
            else:
                # If interrupted, send Stop command to TTS
                if tts_ws and tts_ws.open:
                    await tts_ws.send(json.dumps({"type": "Stop"}))
                # Cancel the TTS task
                if self.tts_task:
                    self.tts_task.cancel()
                    self.tts_task = None

            # Wait for tts_task to complete
            try:
                await self.tts_task
            except asyncio.CancelledError:
                pass

            await tts_ws.close()

        except asyncio.CancelledError:
            print("OpenAI API call was cancelled.")
            # Ensure TTS task and websocket are properly closed
            if self.tts_task:
                self.tts_task.cancel()
            if tts_ws and not tts_ws.closed:
                await tts_ws.close()
        except Exception as e:
            print(f"Error in generate_ai_response: {e}")

    async def listen_deepgram_tts(self, tts_ws):
        try:
            async for message in tts_ws:
                if isinstance(message, bytes):
                    if self.speaking and not self.interrupt_speech:
                        if not hasattr(self, "tts_start_time"):
                            self.tts_start_time = time.time()  # Start timing TTS
                        payload = base64.b64encode(message).decode()
                        response = {
                            "event": "media",
                            "streamSid": self.stream_sid,
                            "media": {"payload": payload},
                        }
                        await self.send(text_data=json.dumps(response))
                else:
                    # Handle non-bytes messages (likely JSON)
                    data = json.loads(message)
                    print(f"TTS Message: {data}")  # Log the TTS message
                    if data.get("type") == "Finished":
                        # TTS has finished processing
                        print("TTS processing finished.")
                        if hasattr(self, "tts_start_time"):
                            tts_end_time = time.time()
                            tts_total_time = tts_end_time - self.tts_start_time
                            print(f"TTS processing time: {tts_total_time:.2f} seconds")
                            del self.tts_start_time
                        self.tts_finished.set()  # Signal that TTS has finished
        except asyncio.CancelledError:
            print("listen_deepgram_tts task was cancelled.")
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Deepgram TTS connection closed: {e}")

    async def send_clear_message(self):
        """
        Send a 'clear' message to Twilio to stop the playback of any buffered audio.
        """
        clear_message = {"event": "clear", "streamSid": self.stream_sid}
        await self.send(text_data=json.dumps(clear_message))
        print("Sent 'clear' message to Twilio to stop playback.")
