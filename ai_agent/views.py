from django.shortcuts import render

from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .utils import generate_voice
from twilio.rest import Client
from datetime import datetime
from calls.models import Call
from calls.serializers import CallSerializer
from django.contrib.auth import get_user_model
import pandas as pd
import logging
import os

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
    if request.method == 'POST':
        try:
            # Parse incoming request data
            data = JSONParser().parse(request)

            # Fetch the user based on the created_by field in the data
            user = User.objects.get(id=data.get('created_by'))

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

                # Initiate the Twilio call
                call = twilio_client.calls.create(
                    from_=from_phone_number,
                    to=client_phone_number,
                    url=f"http://{request.get_host()}/greet-client"
                )

                # Log the call SID and status
                logger.info(f"Call initiated: {client_phone_number}, SID: {call.sid}")

                # Update the CallLog or any related model with the call SID
                Call.objects.create(
                    customer_name=client_name,
                    customer_phone=client_phone_number,
                    call_sid=call.sid,
                    consent_given=consent  # Initially set to False
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

@csrf_exempt
def greet_client(request):
    if request.method not in ['GET', 'POST']:
        return JsonResponse(status=405)
    
    # Retrieve the CallLog based on the call SID
    call_sid = request.POST.get('CallSid') or request.GET.get('CallSid')
    try:
        call_log = Call.objects.get(call_sid=call_sid)
    except Call.DoesNotExist:
        logger.error(f"CallLog with SID {call_sid} does not exist.")
        return JsonResponse(status=404)
    
    greeting_text = (
        f"Hello {call_log.customer_name}, this is Ginie from Army of Me. I hope you're doing well today! "
        "We provide a range of accounting and financial services, including bookkeeping, tax preparation, payroll processing, and more. "
        "Is there a particular service you are interested in, or would you like an overview of our offerings?"
    )
    try:
        audio_url = generate_voice(greeting_text)
    except Exception as e:
        logger.error(f"Error generating voice: {e}")
        return JsonResponse(status=500)
    
    response = f"""
    <Response>
        <Play>{audio_url}</Play>
        <Gather input="speech" action="/gather-input/" method="POST" timeout="15" speechTimeout="auto"/>
    </Response>
    """
    logger.info(f"Greeting and service intro played for: {call_log.customer_name}")
    return JsonResponse(response, content_type='text/xml')

@csrf_exempt
def gather_input(request):
    if request.method != 'POST':
        return JsonResponse(status=405)
    
    user_input = request.POST.get('SpeechResult')
    call_sid = request.POST.get('CallSid')
    
    try:
        call_log = Call.objects.get(call_sid=call_sid)
    except Call.DoesNotExist:
        logger.error(f"CallLog with SID {call_sid} does not exist.")
        return JsonResponse(status=404)
    
    if user_input and user_input.strip():
        logger.info(f"User input received: {user_input}")
        
        if "thank you" in user_input.lower() or "thanks" in user_input.lower():
            logger.info("Customer is satisfied. Ending call.")
            response = respond_and_end_call("Thank you for your time!")
            return response
        
        # Determine AI response based on conversation context
        # Implement your AI response logic here. For simplicity, we'll use a static response.
        ai_response = "Thank you for your query. Our team will contact you shortly."
        
        try:
            audio_url = generate_voice(ai_response)
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            return JsonResponse(status=500)
        
        response = f"""
        <Response>
            <Play>{audio_url}</Play>
            <Gather input="speech" action="/gather-input/" method="POST" timeout="15" speechTimeout="auto"/>
        </Response>
        """
        return JsonResponse(response, content_type='text/xml')
    
    # If no input is received, repeat the request for input
    response = """
    <Response>
        <Gather input="speech" action="/gather-input/" method="POST" timeout="15" speechTimeout="auto"/>
    </Response>
    """
    return JsonResponse(response, content_type='text/xml')

def respond_and_end_call(final_message):
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
