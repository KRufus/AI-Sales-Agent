
import time
import asyncio
from .utils import response_for_gpt, convert_text_to_speech
from .twilio import twilio_client
from .redis_cache import store_public_url
from django.conf import settings




def process_ai_response_logic(call_sid, speech_result):
    try:
        start_time = time.time()

        # Generate AI response
        ai_response_start = time.time()
        ai_response = asyncio.run(response_for_gpt(speech_result))
        ai_response_end = time.time()
        print(f"Time taken to generate AI response: {ai_response_end - ai_response_start:.2f} seconds")

        # Convert AI response to speech
        SPEAK_TEXT = {"text": ai_response}
        tts_start = time.time()
        public_url = asyncio.run(convert_text_to_speech(SPEAK_TEXT, prefix="ai"))
        tts_end = time.time()
        print(f"Time taken for text-to-speech conversion: {tts_end - tts_start:.2f} seconds")

        # print("Before Storing results: ", public_url_storage)
        # Store the public URL for later retrieval
        store_public_url(call_sid, public_url)
        # print("After Storing results: ", public_url_storage)
        
        # Build the URL to the new TwiML endpoint
        play_response_url = f"{settings.EXTERNAL_NGROK_URL}api/ai/play-ai-response/?call_sid={call_sid}"

        # Update the call with the new TwiML URL
        call_update_start = time.time()
        call = twilio_client.calls(call_sid).fetch()
        print(f"Call status before update: {call.status}")
        if call.status in ['queued', 'ringing', 'in-progress']:
            update = twilio_client.calls(call_sid).update(
                url=play_response_url,
                method='POST'
            )
            print(f"Call update result: {update}")
        else:
            print(f"Call {call_sid} is no longer active.")
        call_update_end = time.time()
        print(f"Time taken to update the call: {call_update_end - call_update_start:.2f} seconds")

        total_time = time.time() - start_time
        print(f"Total time taken in process_ai_response: {total_time:.2f} seconds")
    except Exception as e:
        print(f"Error in process_ai_response_logic: {e}")
        import traceback
        traceback.print_exc()
