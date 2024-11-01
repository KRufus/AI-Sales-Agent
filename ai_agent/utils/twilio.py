from django.conf import settings
from twilio.rest import Client

from_phone_number = settings.TWILIO_PHONE_NUMBER

twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)