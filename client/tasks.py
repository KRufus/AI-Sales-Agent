# client/tasks.py
import requests
from celery import shared_task
from .models import Client
from django.conf import settings
from user_auth.models import CustomUser
import logging

logger = logging.getLogger(__name__)

@shared_task
def execute_calls_for_user(created_by_id):
    try:
        # Fetch the user and set is_executing to True
        user = CustomUser.objects.get(id=created_by_id)
        user.is_executing = True
        user.save()
        
        logger.info("changed usert to %s", user)

        logger.info("execute_calls_for_user inside the database")

        pending_clients = Client.objects.filter(
            created_by_id=created_by_id,
            call_status=Client.STATUS_PENDING
        )
        
        logger.info(f"Pending clients: {pending_clients}")

        for client in pending_clients:
            if client.is_called:
                continue

            api_data = {
            "created_by": created_by_id,
            "customer_name": client.name,
            "customer_phone": str(client.phone_number),  # Assuming phone_number is a PhoneNumberField
            "consent": True,  # Assuming consent is required; adjust as necessary
            "assistant": 1,
            "session_name":"Session"
        }

            try:
                response = requests.post(
                    url=f"http://localhost:8000/api/ai/make-call-in-celery/",
                    json=api_data,
                    # headers={"Authorization": f"Bearer {settings.API_TOKEN}"},
                )

                # Log the raw response to see what's returned
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Raw response text: {response.text}")

                # Now try to parse the response
                response_data = response.json()

                logger.info(f"Response JSON: {response_data}")

                if response.status_code == 200:
                    client.is_called = True
                    client.call_status = Client.STATUS_COMPLETED
                    client.save()

                    logger.info(f"Call executed successfully for client {client.name}.")
                else:
                    logger.error(f"Call failed for client {client.name}. Error: {response_data.get('error')}")

            except Exception as e:
                logger.error(f"Error during API call for client {client.name}: {str(e)}")

    except Exception as e:
        logger.error(f"Error executing calls: {str(e)}")
    
    finally:
        # Ensure is_executing is set to False even if there's an error
        user.is_executing = False
        user.save()

    return f"Executed calls for {pending_clients.count()} clients."
