import requests
from celery import shared_task
from .models import Client
from django.conf import settings
from user_auth.models import CustomUser
from assistant.models import Assistant
from assistant.serializers import AssistantSerializer
import logging
import json
# from ai_agent.utils.redis_cache import CacheManager
from .utils import cache_twilio_configs, cache_greeting_message_assistant, cache_prompt_message_for_user

logger = logging.getLogger(__name__)

# @shared_task
# def execute_calls_for_user(created_by_id, assistant, session_name):
#     try:
#         logger.info(f"User started executing calls.{created_by_id} and {assistant}")
        
#         user = CustomUser.objects.get(id=created_by_id)
#         user.is_executing = True
#         user.save()
        
#         assistant_call = Assistant.objects.get(id=assistant, created_by=created_by_id)
#         serializer = AssistantSerializer(assistant_call)
#         assistant_data = serializer.data 
    
        
#         assistant_json = json.dumps(assistant_data)
        
        
#         # {
#         #   "id": 1,
#         #   "created_by": "testuser",
#         #   "config_data": {
#         #     "id": 1,
#         #     "created_by": "testuser",
#         #     "assistants": [
#         #       {
#         #         "id": 1,
#         #         "name": "My Assistant 2"
#         #       }
#         #     ],
#         #     "label": "My Twilio Configuration",
#         #     "twilio_no": "+1234567890",
#         #     "account_sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
#         #     "auth_token": "your_auth_token_here",
#         #     "created_on": "2024-10-21T16:44:12.066245Z",
#         #     "updated_on": "2024-10-21T16:44:12.066245Z"
#         #   },
#         #   "config": 1,
#         #   "name": "My Assistant 2",
#         #   "prompt": "Hello, how can I assist you?",
#         #   "greeting_message": "Welcome!",
#         #   "max_tokens": 150,
#         #   "idle_timeout": 300,
#         #   "max_idle_messages": 5,
#         #   "idle_message": "Are you still there?",
#         #   "is_publish": false,
#         #   "created_on": "2024-10-21T16:44:19.186700Z",
#         #   "updated_on": "2024-10-21T16:44:19.186700Z"
#         # }
        
#         # print(assistant_json, "assistant_json")
#         logger.info(f"Before cache")
#         # user_config = CacheManager.get_user_config(created_by_id)
#         # logger.info(f"inside task {user_config} with id {created_by_id}")
        
#         # if not user_config:
#         # # If not in cache, fetch from the database (assuming you have a UserConfig model)
#         # # This example assumes a UserConfig model exists with user_id, twilio_sid, twilio_token, and prompt fields.
#         #     # user_data = CustomUser.objects.get(id=created_by_id)
        
#         #     # Cache the user config
#         #     CacheManager.set_user_config(
#         #         user_id=created_by_id,
#         #         twilio_no=assistant_json.twilio_no,
#         #         twilio_sid=assistant_json.account_sid,
#         #         twilio_token=assistant_json.auth_token,
#         #         prompt=assistant_json.prompt,
#         #         greeting_message=assistant_json.greeting_message,
#         #         ttl_seconds=3600
#         #     )
        
#             # # Set user_config to the newly fetched data for the call
#             # user_config = {
#             #     "twilio_sid": assistant_json.twilio_sid,
#             #     "twilio_token": assistant_json.twilio_token,
#             #     "prompt": assistant_json.prompt
#             # }
        
#         logger.info(f"User {assistant_json} getting .")
        
#         # logger.info(f"User {CacheManager.get_user_config(created_by_id)} getting cached data.")
        
        
#         # cache_assistant_config_details(created_by_id, assistant_json)
        
#         cache_twilio_configs(created_by_id, {
#             "twilio_no":assistant_json.config_data.twilio_no,
#             "twilio_sid":assistant_json.config_data.account_sid,
#             "twilio_token":assistant_json.config_data.auth_token,
#         })
        
#         cache_greeting_message_assistant(created_by_id, {
#             "greeting_message":assistant_json.greeting_message
#         })
        
#         cache_prompt_message_for_user(created_by_id, {
#             "prompt":assistant_json.prompt
#         })

#         # logger.info(f"User {user.username} started executing calls.")

#         pending_clients = Client.objects.filter(
#             created_by_id=created_by_id,
#             call_status=Client.STATUS_PENDING
#         )
#         logger.info(f"Pending clients: {pending_clients}")

#         for client in pending_clients:
#             if client.is_called:
#                 logger.info(f"Client {client.name} already called, skipping.")
#                 continue


#             client.call_status = Client.STATUS_ONGOING
#             client.save()

#             logger.info(f"Status for client {client.name} set to Ongoing.")

#             api_data = {
#                 "created_by": created_by_id,
#                 "customer_name": client.name,
#                 "customer_phone": str(client.phone_number),
#                 "consent": True,
#                 "assistant": assistant,
#                 "session_name": session_name
#             }

#             try:
#                 logger.info(f"Making AI call for client {client.name}.")
                
#                 response = requests.post(
#                     url=f"http://localhost:8000/api/ai/make-call/",
#                     json=api_data,
#                 )

#                 if response.status_code == 200:
#                     response_data = response.json()
#                     logger.info(f"API Call success for {client.name}, response: {response_data}")

#                     # client.is_called = True
#                     # client.call_status = Client.STATUS_COMPLETED
#                     # client.save()

#                     logger.info(f"Call executed successfully for client {client.name} and marked as Completed.")
#                 else:
#                     logger.error(f"API Call failed for {client.name} with status {response.status_code}")
#                     client.call_status = Client.STATUS_CANCELLED
#                     client.save()

#             except Exception as e:
#                 logger.error(f"Error during API call for client {client.name}: {str(e)}")
#                 client.call_status = Client.STATUS_CANCELLED
#                 client.save()

#     except Exception as e:
#         logger.error(f"Error executing calls: {str(e)}")

#     finally:
#         user.is_executing = False
#         user.save()
#         logger.info(f"User {user.username} finished executing calls.")

#     return f"Executed calls for {pending_clients.count()} clients."


@shared_task
def execute_calls_for_user(created_by_id, assistant, session_name):
    try:
        logger.info(f"User started executing calls.{created_by_id} and {assistant}")

        user = CustomUser.objects.get(id=created_by_id)
        user.is_executing = True
        user.save()

        assistant_call = Assistant.objects.get(id=assistant, created_by=created_by_id)
        serializer = AssistantSerializer(assistant_call)
        assistant_json = serializer.data

        # assistant_json = json.dumps(assistant_data)

        logger.info(f"Before cache")

        cache_twilio_configs(created_by_id, {
            "twilio_no": assistant_json["config_data"]["twilio_no"],
            "twilio_sid": assistant_json["config_data"]["account_sid"],
            "twilio_token": assistant_json["config_data"]["auth_token"],
        })

        cache_greeting_message_assistant(created_by_id, {
            "greeting_message": assistant_json["greeting_message"]
        })

        cache_prompt_message_for_user(created_by_id, {
            "prompt": assistant_json["prompt"]
        })

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

                    client.is_called = True
                    client.call_status = Client.STATUS_COMPLETED
                    client.save()

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
        pending_clients = []  # Set pending_clients to an empty list in case of an error

    finally:
        user.is_executing = False
        user.save()
        logger.info(f"User {user.username} finished executing calls.")

    return f"Executed calls for {len(pending_clients)} clients."
