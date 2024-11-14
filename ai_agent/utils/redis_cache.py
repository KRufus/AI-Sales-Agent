
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# def store_public_url(call_sid, public_url):
#     """
#     Stores the public URL in Redis as part of a list associated with the call_sid.
#     """
#     cache_key = f"public_url_list:{call_sid}"
#     try:
#         # Directly use the Redis client
#         cache.client.get_client().rpush(cache_key, public_url)
#         logger.info(f"Stored public URL for Call SID {call_sid}: {public_url}")
#     except Exception as e:
#         logger.error(f"Failed to store public URL for Call SID {call_sid}: {public_url}. Error: {e}")
        


# def retrieve_public_url(call_sid):
#     """
#     Retrieves and removes the first public URL from Redis list associated with the call_sid.
#     Returns the URL if found, else returns None.
#     """
#     cache_key = f"public_url_list:{call_sid}"
#     try:
#         # Directly use the Redis client
#         public_url = cache.client.get_client().lpop(cache_key)
#         if public_url:
#             public_url = public_url.decode('utf-8')  # Decode bytes to string
#             logger.info(f"Retrieved and removed public URL for Call SID {call_sid}: {public_url}")
#         else:
#             logger.warning(f"No public URL found for Call SID {call_sid}")
#         return public_url
#     except Exception as e:
#         logger.error(f"Failed to retrieve public URL for Call SID {call_sid}. Error: {e}")
#         return None
    

# cache_manager.py

# from django.core.cache import cache

class CacheManager:
    
    @staticmethod
    def set_user_config(user_id, twilio_no, twilio_sid, twilio_token, prompt, greeting_message, ttl_seconds=None):
        
        logger.info(f"entering.... {user_id} to {twilio_no}")
        """
        Store Twilio config and prompt for a specific user in Redis.
        
        :param user_id: Unique identifier for the user
        :param twilio_sid: Twilio Account SID
        :param twilio_token: Twilio Auth Token
        :param prompt: Prompt text for the user
        :param ttl_seconds: Optional time-to-live for the cache entry
        """
        cache_key = f"user:{user_id}:config"
        data = {
            "twilio_no": twilio_no,
            "twilio_sid": twilio_sid,
            "twilio_token": twilio_token,
            "prompt": prompt,
            "greeting_message":greeting_message,
        }
        for_cache = cache.set(cache_key, data, timeout=ttl_seconds)
        logger.info(f"Setted the cache {cache_key} to {data}")

    @staticmethod
    def get_user_config(user_id):
        """
        Retrieve Twilio config and prompt for a specific user from Redis.
        
        :param user_id: Unique identifier for the user
        :return: Dictionary with 'twilio_sid', 'twilio_token', and 'prompt', or None if not cached
        """
        
        logger(f"Before calling Twilio")
        cache_key = f"user:{user_id}:config"
        logger.info(f"{cache_key} cache key")
        return cache.get(cache_key)

    @staticmethod
    def delete_user_config(user_id):
        """
        Delete the cached Twilio config and prompt for a specific user.
        
        :param user_id: Unique identifier for the user
        """
        cache_key = f"user:{user_id}:config"
        cache.delete(cache_key)

