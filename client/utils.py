from django.core.cache import cache
import logging


logger = logging.getLogger(__name__)


def cache_assistant_config_details(created_by, data):

    cache_key = f"assistant:-{created_by}"
    logger.info(f"created by ->  {cache_key}")

    try:
        cache.client.get_client().rpush(cache_key, data)
        # cache.client.get_client().hset(cache_key, field="config_data", value=data)

        logger.info(f"Stored assistant and config {data}")
    except Exception as e:
        logger.error(f"Failed to store  {data}. Error: {e}")


def retrieve_assistant_config_details(created_by):

    cache_key = f"assistant:-{created_by}"
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
