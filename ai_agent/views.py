
import random
import string
import time
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .utils.utils import convert_text_to_speech, response_for_gpt
from twilio.rest import Client
from datetime import datetime
from calls.models import Call
from calls.serializers import CallSerializer
from django.contrib.auth import get_user_model
import pandas as pd
import logging
import os
from .utils.utils import dg_client
import asyncio
from django.conf import settings
from twilio.twiml.voice_response import VoiceResponse, Gather
from deepgram import DeepgramClient
from .utils.utils import twilio_client, from_phone_number
from asgiref.sync import async_to_sync


User = get_user_model()
logger = logging.getLogger(__name__)


DEEPGRAM_API_TOKEN = api_key=os.getenv("DEEPGRAM_API_KEY")
dg_client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))



@csrf_exempt
def make_ai_call(request):
    print("\n\n ______ make_ai_call URL was triggered")
    print("request.get_host() _____ ", request.get_host())

    if request.method == 'POST':
        try:
            data = JSONParser().parse(request)

            user = User.objects.get(id=data.get('created_by'))

            serializer = CallSerializer(data=data)
            if serializer.is_valid():
                call_instance = serializer.save(created_by=user)

                client_phone_number = serializer.validated_data.get('customer_phone')
                client_name = serializer.validated_data.get('customer_name')
                consent = serializer.validated_data.get('consent')

                if not client_phone_number or not client_name:
                    return JsonResponse({"error": "Missing client_phone_number or client_name."}, status=400)
                
                SPEAK_TEXT = {"text":f"Hello Amul, this is Ginie from Army of Me. I hope you're doing well today! We provide a range of accounting and financial services, including bookkeeping, tax preparation, payroll processing, and more. Is there a particular service you are interested in, or would you like an overview of our offerings? "}


                public_url = asyncio.run(convert_text_to_speech(SPEAK_TEXT, prefix="ai"))
                
                if not public_url:
                    return JsonResponse({"error": "Failed to generate TTS or upload to MinIO"}, status=500)
                
                print(public_url, "public_url")
                
                
                response = VoiceResponse()
                
                gather = Gather(
                input="speech dtmf",
                action=f"https://dbb4-103-88-236-42.ngrok-free.app/api/ai/process-gather/",
                method="POST",
                timeout=5,
                speechTimeout="2",
                speechModel="deepgram_nova-2",
                language="en-US"
            )
                gather.play(public_url)
                print(response, "response")
                response.append(gather)
                
    
                call = twilio_client.calls.create(
                    twiml=response,
                    to=client_phone_number,
                    from_=from_phone_number
                )
                
                print("call _____ ", call)
                logger.info(f"Call initiated: {client_phone_number}, SID: {call.sid}")

                Call.objects.create(
                    customer_name=client_name,
                    customer_phone=client_phone_number,
                    call_sid=call.sid,
                    # assistant_id=data.get('assistant_id'),
                    assistant_id=1,
                    # consent_given=consent  # Initially set to False
                )
                

                return JsonResponse({"call_sid": call.sid}, status=status.HTTP_200_OK)

            else:
                return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error initiating AI call: {e}")
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JsonResponse({"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@csrf_exempt
def process_gather(request):
    if request.method == 'POST':
        call_sid = request.POST.get('CallSid')
        print(call_sid, "call_sid_inside the process_gather")

        if not call_sid:
            return JsonResponse({"error": "Call SID is missing"}, status=400)

        speech_result = request.POST.get('SpeechResult')
        print(speech_result, "speechResult")

        try:
            ai_response = async_to_sync(response_for_gpt)(speech_result)
            print(ai_response, "ai_response")

            SPEAK_TEXT = {"text": ai_response}
            public_url = async_to_sync(convert_text_to_speech)(SPEAK_TEXT, prefix="ai")

            response = VoiceResponse()
            gather = Gather(
                input="speech dtmf",
                action=f"https://dbb4-103-88-236-42.ngrok-free.app/api/ai/process-gather/",
                method="POST",
                timeout=5,
                speechTimeout="2",
                speechModel="deepgram_nova-2",
                language="en-US"
            )
            gather.play(public_url)
            response.append(gather)

            return HttpResponse(str(response), content_type='application/xml')
        except Exception as e:
            print(f"Error in process_gather: {e}")
            return HttpResponse(status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


def play_audio_to_user(url, call_sid):
    if not call_sid:
        print("No call SID found.")
        return
    
    try:
        call = twilio_client.calls(call_sid).fetch()
        if call.status not in ['in-progress', 'ringing', 'queued']:
            print(f"Call {call_sid} is not active. Current status: {call.status}")
            return
    except Exception as e:
        print(f"Error fetching call status: {e}")
        return
    
    response = VoiceResponse()
    gather = Gather(
        input="speech dtmf",
        action=f"https://dbb4-103-88-236-42.ngrok-free.app/api/ai/process-gather/",
        method="POST",
        timeout=5,
        speechTimeout="10",
        speechModel="deepgram_nova-2",
        language="en-US"
    )
    gather.play(url)
    response.append(gather)
    
    twilio_client.calls(call_sid).update(twiml=response)
    print("Audio response sent to user from URL:", url)



def log_customer_consent(customer_name, customer_phone, call_sid):
    Call.objects.create(customer_name=customer_name, customer_phone=customer_phone, call_sid=call_sid, consent_given=True)


def log_customer_consent_to_excel(customer_name, customer_phone):
    file_path = "customer_interest_log.xlsx"
    df = pd.read_excel(file_path) if os.path.exists(file_path) else pd.DataFrame(columns=["Customer Name", "Phone Number", "Consent Given", "Time"])
    new_entry = {
        "Customer Name": customer_name,
        "Phone Number": customer_phone,
        "Consent Given": "Yes",
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_excel(file_path, index=False)
    
    
@csrf_exempt
def make_ai_call_in_celery(request):
    if request.method == 'POST':
        try:
            
            data = JSONParser().parse(request)
            
            created_by_id = data.get('created_by')

           
            user = User.objects.get(id=data.get('created_by'))

            
            serializer = CallSerializer(data=data)
            if serializer.is_valid():
                
                call_instance = serializer.save(created_by=user)

               
                client_phone_number = serializer.validated_data.get('customer_phone')
                client_name = serializer.validated_data.get('customer_name')
                consent = serializer.validated_data.get('consent')
                assistant = serializer.validated_data.get('assistant')
                session_name = serializer.validated_data.get('session_name')

                if not client_phone_number or not client_name:
                    return JsonResponse({"error": "Missing client_phone_number or client_name."}, status=400)


                time.sleep(1 * 60)
                fake_sid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=34))

                
                logger.info(f"Fake call initiated for demo: {client_phone_number}, SID: {fake_sid}")

                
                Call.objects.create(
                    session_name=session_name,
                    assistant=assistant,
                    customer_name=client_name,
                    customer_phone=client_phone_number,
                    created_by=user,
                    consent=consent,
                )
                
                print("call created successfully")

                
                return JsonResponse({"call_sid": fake_sid}, status=status.HTTP_200_OK)

            else:
                
                return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error initiating fake AI call: {e}")
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JsonResponse({"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)




