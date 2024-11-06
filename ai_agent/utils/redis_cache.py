
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

def store_public_url(call_sid, public_url):
    """
    Stores the public URL in Redis as part of a list associated with the call_sid.
    """
    cache_key = f"public_url_list:{call_sid}"
    try:
        # Directly use the Redis client
        cache.client.get_client().rpush(cache_key, public_url)
        logger.info(f"Stored public URL for Call SID {call_sid}: {public_url}")
    except Exception as e:
        logger.error(f"Failed to store public URL for Call SID {call_sid}: {public_url}. Error: {e}")
        


def retrieve_public_url(call_sid):
    """
    Retrieves and removes the first public URL from Redis list associated with the call_sid.
    Returns the URL if found, else returns None.
    """
    cache_key = f"public_url_list:{call_sid}"
    try:
        # Directly use the Redis client
        public_url = cache.client.get_client().lpop(cache_key)
        if public_url:
            public_url = public_url.decode('utf-8')  # Decode bytes to string
            logger.info(f"Retrieved and removed public URL for Call SID {call_sid}: {public_url}")
        else:
            logger.warning(f"No public URL found for Call SID {call_sid}")
        return public_url
    except Exception as e:
        logger.error(f"Failed to retrieve public URL for Call SID {call_sid}. Error: {e}")
        return None
