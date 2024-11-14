import random
import string
import time
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .utils.utils import convert_text_to_speech, response_for_gpt


# from twilio.rest import Client
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
from threading import Thread
from .tasks import process_ai_response_task
from .utils.redis_cache import retrieve_public_url
from client.models import Client
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from client.utils import retrieve_assistant_config_details



User = get_user_model()
logger = logging.getLogger(__name__)




DEEPGRAM_API_TOKEN = api_key = os.getenv("DEEPGRAM_API_KEY")
dg_client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))




@csrf_exempt
def get_twiml(request):
   file_path = os.path.join(settings.BASE_DIR, "ai_agent", "templates", "streams.xml")
   with open(file_path, "rb") as f:
       content = f.read()
   return HttpResponse(content, content_type="text/xml")




@csrf_exempt
def make_ai_call(request):
   print("\n\n ______ make_ai_call URL was triggered")
   print("request.get_host() _____ ", request.get_host())


   if request.method == "POST":
       try:
           data = JSONParser().parse(request)


           user = User.objects.get(id=data.get("created_by"))


           print(data, "data")
           
           cache_data = retrieve_assistant_config_details(user)
           
           print(cache_data, "cache_data")


           serializer = CallSerializer(data=data)
           if serializer.is_valid():
               call_instance = serializer.save(created_by=user)


               client_phone_number = serializer.validated_data.get("customer_phone")
               client_name = serializer.validated_data.get("customer_name")
               consent = serializer.validated_data.get("consent")


               if not client_phone_number or not client_name:
                   return JsonResponse(
                       {"error": "Missing client_phone_number or client_name."},
                       status=400,
                   )


               call = twilio_client.calls.create(
                   to=client_phone_number,
                   from_=from_phone_number,
                   url="https://9c66-106-79-199-14.ngrok-free.app/api/ai/twiml/",
               )


               print("call _____ ", call)
               logger.info(f"Call initiated: {client_phone_number}, SID: {call.sid}")


               Call.objects.create(
                   customer_name=client_name,
                   customer_phone=client_phone_number,
                   call_sid=call.sid,
                   assistant_id=data.get(
                       "assistant_id", 1
                   ),
               )


               return JsonResponse({"call_sid": call.sid}, status=status.HTTP_200_OK)


           else:
               return JsonResponse(
                   serializer.errors, status=status.HTTP_400_BAD_REQUEST
               )


       except User.DoesNotExist:
           return JsonResponse(
               {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
           )
       except Exception as e:
           logger.error(f"Error initiating AI call: {e}")
           return JsonResponse(
               {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
           )


   return JsonResponse(
       {"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED
   )



@csrf_exempt
def make_ai_call_in_celery(request):
   if request.method == "POST":
       try:


           data = JSONParser().parse(request)


           created_by_id = data.get("created_by")


           user = User.objects.get(id=data.get("created_by"))


           serializer = CallSerializer(data=data)
           if serializer.is_valid():


               call_instance = serializer.save(created_by=user)


               client_phone_number = serializer.validated_data.get("customer_phone")
               client_name = serializer.validated_data.get("customer_name")
               consent = serializer.validated_data.get("consent")
               assistant = serializer.validated_data.get("assistant")
               session_name = serializer.validated_data.get("session_name")


               if not client_phone_number or not client_name:
                   return JsonResponse(
                       {"error": "Missing client_phone_number or client_name."},
                       status=400,
                   )


               time.sleep(1 * 60)
               fake_sid = "".join(
                   random.choices(string.ascii_uppercase + string.digits, k=34)
               )


               logger.info(
                   f"Fake call initiated for demo: {client_phone_number}, SID: {fake_sid}"
               )


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


               return JsonResponse(
                   serializer.errors, status=status.HTTP_400_BAD_REQUEST
               )


       except User.DoesNotExist:
           return JsonResponse(
               {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
           )
       except Exception as e:
           logger.error(f"Error initiating fake AI call: {e}")
           return JsonResponse(
               {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
           )


   return JsonResponse(
       {"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED
   )



