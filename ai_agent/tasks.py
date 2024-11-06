from celery import shared_task
from .utils.ai_logic import process_ai_response_logic

@shared_task
def process_ai_response_task(call_sid, speech_result):
    process_ai_response_logic(call_sid, speech_result)
