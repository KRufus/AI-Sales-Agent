import requests
from celery import shared_task
from .models import Client
from django.conf import settings
from user_auth.models import CustomUser
from assistant.models import Assistant
from assistant.serializers import AssistantSerializer
import logging
import json
from .utils import cache_assistant_config_details, retrieve_assistant_config_details

logger = logging.getLogger(__name__)

@shared_task
def execute_calls_for_user(created_by_id, assistant, session_name):
    try:
        logger.info(f"User started executing calls.{created_by_id} and {assistant}")
        
        user = CustomUser.objects.get(id=created_by_id)
        user.is_executing = True
        user.save()
        
        assistant_call = Assistant.objects.get(id=assistant, created_by=created_by_id)
        serializer = AssistantSerializer(assistant_call)
        assistant_data = serializer.data 
        
        assistant_json = json.dumps(assistant_data)
        
        # logger.info(f"User {assistant_json} getting .")
        
        cache_assistant_config_details(created_by_id, assistant_json)

        # logger.info(f"User {user.username} started executing calls.")

        pending_clients = Client.objects.filter(
            created_by_id=created_by_id,
            call_status=Client.STATUS_PENDING
        )
        logger.info(f"Pending clients: {pending_clients}")

        for client in pending_clients:
            if client.is_called:
                logger.info(f"Client {client.name} already called, skipping.")
                continue


            client.call_status = Client.STATUS_ONGOING
            client.save()

            logger.info(f"Status for client {client.name} set to Ongoing.")

            api_data = {
                "created_by": created_by_id,
                "customer_name": client.name,
                "customer_phone": str(client.phone_number),
                "consent": True,
                "assistant": assistant,
                "session_name": session_name
            }

            try:
                logger.info(f"Making AI call for client {client.name}.")
                
                response = requests.post(
                    url=f"http://localhost:8000/api/ai/make-call/",
                    json=api_data,
                )

                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"API Call success for {client.name}, response: {response_data}")

                    # client.is_called = True
                    # client.call_status = Client.STATUS_COMPLETED
                    # client.save()

                    logger.info(f"Call executed successfully for client {client.name} and marked as Completed.")
                else:
                    logger.error(f"API Call failed for {client.name} with status {response.status_code}")
                    client.call_status = Client.STATUS_CANCELLED
                    client.save()

            except Exception as e:
                logger.error(f"Error during API call for client {client.name}: {str(e)}")
                client.call_status = Client.STATUS_CANCELLED
                client.save()

    except Exception as e:
        logger.error(f"Error executing calls: {str(e)}")

    finally:
        user.is_executing = False
        user.save()
        logger.info(f"User {user.username} finished executing calls.")

    return f"Executed calls for {pending_clients.count()} clients."
