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
        # Set the user as executing calls
        user = CustomUser.objects.get(id=created_by_id)
        user.is_executing = True
        user.save()

        logger.info(f"User {user.username} started executing calls.")

        # Get the pending clients for the user
        pending_clients = Client.objects.filter(
            created_by_id=created_by_id,
            call_status=Client.STATUS_PENDING
        )
        logger.info(f"Pending clients: {pending_clients}")

        # Iterate over each pending client and process the call
        for client in pending_clients:
            if client.is_called:
                logger.info(f"Client {client.name} already called, skipping.")
                continue

            # Update the status to ongoing before making the call
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
                
                # Make the API call
                response = requests.post(
                    url=f"http://localhost:8000/api/ai/make-call-in-celery/",
                    json=api_data,
                )

                # Ensure the request was successful
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"API Call success for {client.name}, response: {response_data}")

                    # Mark client as completed
                    client.is_called = True
                    client.call_status = Client.STATUS_COMPLETED
                    client.save()

                    logger.info(f"Call executed successfully for client {client.name} and marked as Completed.")
                else:
                    logger.error(f"API Call failed for {client.name} with status {response.status_code}")
                    # Mark as cancelled if the call fails
                    client.call_status = Client.STATUS_CANCELLED
                    client.save()

            except Exception as e:
                # If an error occurs during the API call, mark the client as cancelled
                logger.error(f"Error during API call for client {client.name}: {str(e)}")
                client.call_status = Client.STATUS_CANCELLED
                client.save()

    except Exception as e:
        logger.error(f"Error executing calls: {str(e)}")

    finally:
        # Mark the user as no longer executing calls
        user.is_executing = False
        user.save()
        logger.info(f"User {user.username} finished executing calls.")

    return f"Executed calls for {pending_clients.count()} clients."
