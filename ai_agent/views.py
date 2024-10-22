from django.shortcuts import render
import random
import string
import time

from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import sync_to_async
from .utils import generate_voice
from twilio.rest import Client
from datetime import datetime
from calls.models import Call
from calls.serializers import CallSerializer
from django.contrib.auth import get_user_model
import pandas as pd
import logging
import os
from .utils import dg_client
import asyncio
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)

twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
from_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

# @csrf_exempt
# def make_ai_call(request):
#     logger.info('______ make_ai_call URL was triggered')
#     return JsonResponse({"status": "success", "message": "AI call initiated"}, status=200)

#     if request.method != 'POST':
#         return JsonResponse({"error": "Invalid request method."}, status=405)
    
#     client_phone_number = request.POST.get('client_phone_number')
#     client_name = request.POST.get('client_name')

#     if not client_phone_number or not client_name:
#         return JsonResponse({"error": "Missing client_phone_number or client_name."}, status=400)

#     try:
#         call = twilio_client.calls.create(
#             from_=from_phone_number,
#             to=client_phone_number,
#             url=f"http://{request.get_host()}/greet-client"
#         )
#         logger.info(f"Call initiated: {client_phone_number}, SID: {call.sid}")
        
#         # Log the call in CallLog model
#         CallLog.objects.create(
#             customer_name=client_name,
#             customer_phone=client_phone_number,
#             call_sid=call.sid,
#             consent_given=False  # Initially set to False
#         )
        
#         return JsonResponse({"call_sid": call.sid}, status=200)
#     except Exception as e:
#         logger.error(f"Error initiating call: {e}")
#         return JsonResponse({"error": str(e)}, status=500)

# @csrf_exempt
# # @api_view(['POST'])
# def make_ai_call(request):
#     if request.method == 'POST':
#         # Parse the incoming request data
#         data = JSONParser().parse(request)

#         user = User.objects.get(id=data.get('created_by'))
#         # Use the serializer to validate and create the Call instance
#         serializer = CallSerializer(data=data)

#         if serializer.is_valid():
#             # Save the new Call instance using the serializer
#             serializer.save(created_by=user)

#             # Return the created Call data
#             return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             # Return validation errors if the serializer is not valid
#             return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     return JsonResponse({"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)



@csrf_exempt
def make_ai_call(request):
    print("\n\n ______ make_ai_call URL was triggered")
    print("request.get_host() _____ ", request.get_host())
    # print("request.host _____ ", request.host)
    if request.method == 'POST':
        try:
            # Parse incoming request data
            data = JSONParser().parse(request)
            print("data _____ ", data)

            # Fetch the user based on the created_by field in the data
            user = User.objects.get(id=data.get('created_by'))
            print("user _____ ", user)

            # Use serializer to validate and create Call instance
            serializer = CallSerializer(data=data)
            if serializer.is_valid():
                # Save the new Call instance
                call_instance = serializer.save(created_by=user)

                # Extract phone number and other details from the validated data
                client_phone_number = serializer.validated_data.get('customer_phone')
                client_name = serializer.validated_data.get('customer_name')
                consent = serializer.validated_data.get('consent')

                if not client_phone_number or not client_name:
                    return JsonResponse({"error": "Missing client_phone_number or client_name."}, status=400)

                url=f"https://e613-103-88-236-42.ngrok-free.app/api/ai/greet-client/"
                print("url _____ ", url)
                # Initiate the Twilio call
                call = twilio_client.calls.create(
                    from_=from_phone_number,
                    to=client_phone_number,
                    url=f"https://e613-103-88-236-42.ngrok-free.app/api/ai/greet-client/",
                    record=True,
                )

                print("call _____ ", call)

                # Log the call SID and status
                logger.info(f"Call initiated: {client_phone_number}, SID: {call.sid}")

                # # Update the CallLog or any related model with the call SID
                Call.objects.create(
                    customer_name=client_name,
                    customer_phone=client_phone_number,
                    call_sid=call.sid,
                    # assistant_id=data.get('assistant_id'),
                    assistant_id=1,
                    # consent_given=consent  # Initially set to False
                )

                # Return the response with the call SID
                return JsonResponse({"call_sid": call.sid}, status=status.HTTP_200_OK)

            else:
                # Return validation errors if the serializer is not valid
                return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return JsonResponse({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error initiating AI call: {e}")
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JsonResponse({"error": "Invalid request method."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# async def test_generate_voice():
#     text = (
#         "Hello, this is Ginie from Army of Me. I hope you're doing well today! "
#         "We provide a range of accounting and financial services, including bookkeeping, tax preparation, payroll processing, and more. "
#         "Is there a particular service you are interested in, or would you like an overview of our offerings?"
#     )
#     return await generate_voice(text)


# # Run the test function
# asyncio.run(test_generate_voice())


@csrf_exempt
async def greet_client(request):
    print("\n\n ______ greet_client URL was triggered")

    if request.method not in ['GET', 'POST']:
        return JsonResponse({"error": "Invalid request method."}, status=405)

    # Retrieve the CallLog based on the call SID
    call_sid = request.POST.get('CallSid') or request.GET.get('CallSid')

    if not call_sid:
        return JsonResponse({"error": "Missing CallSid in request."}, status=400)

    logger.info(f"Received call SID: {call_sid}")

    try:
        # Use sync_to_async to run the ORM call in a synchronous context
        call_log = await sync_to_async(Call.objects.get)(call_sid=call_sid)
    except Call.DoesNotExist:
        logger.error(f"CallLog with SID {call_sid} does not exist.")
        # return JsonResponse(status=404)
        return JsonResponse({"error": f"CallLog with SID {call_sid} does not exist."}, status=404)

    greeting_text = (
        f"Hello {call_log.customer_name}, this is Ginie from Army of Me. I hope you're doing well today! "
        "We provide a range of accounting and financial services, including bookkeeping, tax preparation, payroll processing, and more. "
        "Is there a particular service you are interested in, or would you like an overview of our offerings?"
    )

    try:
        # Await the asynchronous generate_voice function
        # audio_url = asyncio.run(test_generate_voice())
        audio_url = await generate_voice(greeting_text)
        
        # audio_url = request.build_absolute_uri(settings.MEDIA_URL + 'output.wav')
        # audio_url = "https://ae8c-103-88-236-42.ngrok-free.app/media/output.wav"
        
        print("\n\n audio_url _____ ", audio_url)

    except Exception as e:
        logger.error(f"Error generating voice: {e}")
        return JsonResponse({"error": "Error generating voice."}, status=500)

    response = f"""
    <Response>
        <Play>{audio_url}</Play>
        <Gather input="speech" action="/gather-input/" method="POST" timeout="15" speechTimeout="auto"/>
    </Response>
    """
    logger.info(f"Greeting and service intro played for: {call_log.customer_name}")
    return JsonResponse(response, content_type='text/xml', safe=False)

# @csrf_exempt
# def gather_input(request):
#     if request.method != 'POST':
#         return JsonResponse(status=405)
    
#     user_input = request.POST.get('SpeechResult')
#     call_sid = request.POST.get('CallSid')
    
#     try:
#         call_log = Call.objects.get(call_sid=call_sid)
#     except Call.DoesNotExist:
#         logger.error(f"CallLog with SID {call_sid} does not exist.")
#         return JsonResponse(status=404)
    
#     if user_input and user_input.strip():
#         logger.info(f"User input received: {user_input}")
        
#         if "thank you" in user_input.lower() or "thanks" in user_input.lower():
#             logger.info("Customer is satisfied. Ending call.")
#             response = respond_and_end_call("Thank you for your time!")
#             return response
        
#         # Determine AI response based on conversation context
#         # Implement your AI response logic here. For simplicity, we'll use a static response.
#         ai_response = "Thank you for your query. Our team will contact you shortly."
        
#         try:
#             audio_url = generate_voice(ai_response)
#         except Exception as e:
#             logger.error(f"Error generating voice: {e}")
#             return JsonResponse(status=500)
        
#         response = f"""
#         <Response>
#             <Play>{audio_url}</Play>
#             <Gather input="speech" action="/gather-input/" method="POST" timeout="15" speechTimeout="auto"/>
#         </Response>
#         """
#         return JsonResponse(response, content_type='text/xml')
    
#     # If no input is received, repeat the request for input
#     response = """
#     <Response>
#         <Gather input="speech" action="/gather-input/" method="POST" timeout="15" speechTimeout="auto"/>
#     </Response>
#     """
#     return JsonResponse(response, content_type='text/xml')



@csrf_exempt
def gather_input(request):
    print("\n\n ______ gather_input URL was triggered")

    if request.method != 'POST':
        return JsonResponse(status=405)

    # Get the speech input from the user (audio)
    audio_file = request.FILES.get('audio_file')  # Assuming Twilio sends an audio file

    if not audio_file:
        return JsonResponse({"error": "No audio file provided."}, status=400)

    try:
        # Process the audio using Deepgram STT
        with open(audio_file, 'rb') as audio_data:
            response = dg_client.transcription.prerecorded({
                "buffer": audio_data,
                "model": "nova",
                "punctuate": True,
                "language": "en-US"
            })

        # Extract the transcription result
        user_input = response['results']['channels'][0]['alternatives'][0]['transcript']
        logger.info(f"User input received: {user_input}")
        
        # Handle the user's input for the conversation
        if "thank you" in user_input.lower():
            return respond_and_end_call("Thank you for your time!")

        ai_response = "Thank you for your query. Our team will contact you shortly."
        audio_url = generate_voice(ai_response)  # Use the updated TTS function
        response = f"""
        <Response>
            <Play>{audio_url}</Play>
            <Gather input="speech" action="/gather-input/" method="POST" timeout="15" speechTimeout="auto"/>
        </Response>
        """
        return JsonResponse(response, content_type='text/xml')

    except Exception as e:
        logger.error(f"Error in Deepgram STT: {e}")
        return JsonResponse(status=500)







def respond_and_end_call(final_message):
    print("\n\n ______ respond_and_end_call URL was triggered")

    try:
        audio_url = generate_voice(final_message)
    except Exception as e:
        logger.error(f"Error generating final voice response: {e}")
        return JsonResponse(status=500)
    
    response = f"""
    <Response>
        <Play>{audio_url}</Play>
        <Hangup/>
    </Response>
    """
    return JsonResponse(response, content_type='text/xml')



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

