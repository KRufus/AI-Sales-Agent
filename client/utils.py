from django.core.cache import cache
import logging
import json


logger = logging.getLogger(__name__)


def cache_twilio_configs(created_by, data):

    cache_key = f"user_twilio_config:-{created_by}"
    logger.info(f"created by ->  {cache_key}")

    try:
        cache.client.get_client().rpush(cache_key, json.dumps(data))
        # cache.client.get_client().hset(cache_key, field="config_data", value=data)
        logger.info(f"Stored assistant and config {data}")
    except Exception as e:
        logger.error(f"Failed to store  {data}. Error: {e}")
        
        
        
def cache_greeting_message_assistant(created_by, data):
    cache_key = f"user_greeting_message_assistant_{created_by}"
    logger.info(f"created by ->  {cache_key}")

    try:
        cache.client.get_client().rpush(cache_key, json.dumps(data))
        # cache.client.get_client().hset(cache_key, field="config_data", value=data)
        logger.info(f"Stored assistant and config {data}")
    except Exception as e:
        logger.error(f"Failed to store  {data}. Error: {e}")
        
        
def cache_prompt_message_for_user(created_by, data):
    cache_key = f"user_prompt_message_{created_by}"
    logger.info(f"created by ->  {cache_key}")

    try:
        cache.client.get_client().rpush(cache_key, json.dumps(data))
        # cache.client.get_client().hset(cache_key, field="config_data", value=data)
        logger.info(f"Stored assistant and config {data}")
    except Exception as e:
        logger.error(f"Failed to store  {data}. Error: {e}")
   
        
        
def cache_assistant_config_details(created_by, data):

    cache_key = f"assistant:-{created_by}"
    logger.info(f"created by ->  {cache_key}")

    try:
        cache.client.get_client().rpush(cache_key, data)
        # cache.client.get_client().hset(cache_key, field="config_data", value=data)
        logger.info(f"Stored assistant and config {data}")
    except Exception as e:
        logger.error(f"Failed to store  {data}. Error: {e}")


def retrieve_twilio_configs(created_by):

    cache_key = f"user_twilio_config:-{created_by}"
    logger.info(f"created by -> at retrive  {cache_key}")

    try:
        assistant = cache.client.get_client().lpop(cache_key)
        # assistant = cache.client.get_client().hget(cache_key, "config_data")
        if assistant:
            assistant = assistant.decode("utf-8")
            # logger.info(f"Retrieved and removed assistant {created_by}: {assistant}")
        else:
            logger.warning(f"No found for assistant {created_by}")
        return assistant
    except Exception as e:
        logger.error(f"Failed to retrieve assistant {created_by}. Error: {e}")
        return None
    
    
def retrieve_greeting_message_assistant(created_by):

    cache_key = f"user_greeting_message_assistant_{created_by}"
    logger.info(f"created by -> at retrive  {cache_key}")
    
    try:
        assistant = cache.client.get_client().lpop(cache_key)
        # assistant = cache.client.get_client().hget(cache_key, "config_data")
        if assistant:
            assistant = assistant.decode("utf-8")
            # logger.info(f"Retrieved and removed assistant {created_by}: {assistant}")
        else:
            logger.warning(f"No found for assistant {created_by}")
        return assistant
    except Exception as e:
        logger.error(f"Failed to retrieve assistant {created_by}. Error: {e}")
        return None
    
def retrieve_prompt_message_for_user(created_by):

    cache_key = f"user_greeting_message_assistant_{created_by}"
    logger.info(f"created by -> at retrive  {cache_key}")
    
    try:
        assistant = cache.client.get_client().lpop(cache_key)
        # assistant = cache.client.get_client().hget(cache_key, "config_data")
        if assistant:
            assistant = assistant.decode("utf-8")
            # logger.info(f"Retrieved and removed assistant {created_by}: {assistant}")
        else:
            logger.warning(f"No found for assistant {created_by}")
        return assistant
    except Exception as e:
        logger.error(f"Failed to retrieve assistant {created_by}. Error: {e}")
        return None
