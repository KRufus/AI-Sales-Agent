
import requests
from celery import shared_task
from .models import Client
from django.conf import settings
from user_auth.models import CustomUser
import logging

logger = logging.getLogger(__name__)

@shared_task
def execute_calls_for_user(created_by_id, assistant, session_name):
    try:
        
        user = CustomUser.objects.get(id=created_by_id)
        user.is_executing = True
        user.save()
        

        pending_clients = Client.objects.filter(
            created_by_id=created_by_id,
            call_status=Client.STATUS_PENDING
        )
        

        for client in pending_clients:
            if client.is_called:
                continue

            api_data = {
            "created_by": created_by_id,
            "customer_name": client.name,
            "customer_phone": str(client.phone_number),
            "consent": True, 
            "assistant": assistant,
            "session_name":session_name
            }
            
            client.call_status = Client.STATUS_ONGOING
            
            client.save()
            
            try:
                response = requests.post(
                    url=f"http://localhost:8000/api/ai/make-call-in-celery/",
                    json=api_data,
                )
                

                response_data = response.json()


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
        user.is_executing = False
        user.save()

    return f"Executed calls for {pending_clients.count()} clients."
