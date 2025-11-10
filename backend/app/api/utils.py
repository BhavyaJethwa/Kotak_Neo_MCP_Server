import redis.asyncio as aioredis
import json
from fastapi import HTTPException
from neo_api_client import NeoAPI

EIGHTEEN_HOURS_IN_SECONDS = 18 * 60 * 60

async def get_redis():
    redis_client = None
    try:
        redis_client = aioredis.Redis(
            host='localhost', 
            port=6379, 
            db=0, 
            decode_responses=True
        )
        await redis_client.ping()
        print("Connected to Redis successfully!")
    except Exception as e: 
        print(f"Could not connect to Redis: {e}")
        redis_client = None
    finally:
        return redis_client
         


# In your validate.py or a separate dependency file

async def get_current_client(x_session_id: str):
    # ... (Redis fetch logic) ...
    redis_key = f"session:{x_session_id}"
    redis_client = await get_redis()
    session_data_json = await redis_client.get(redis_key)
    
    # ... (Error handling) ...

    try:
        session_data = json.loads(session_data_json)
        
        # 1. Initialize Client with the final TRADING_TOKEN
        client = NeoAPI(
            environment=session_data.get("environment"),
            # The TRADING_TOKEN (from totp_validate) is the one required for trading access.
            access_token=session_data.get("TRADING_TOKEN"), 
            neo_fin_key=session_data.get("neo_fin_key"),
            consumer_key=session_data.get("consumer_key"),
        )
        
        # 2. CRITICAL STEP: Manually set the TRADING_SID and BASE_URL
        # The NeoAPI client needs the TRADING_SID/BASE_URL headers for trading endpoints.
        
        # The TRADING_TOKEN from totp_validate is often stored as the internal 'edit_token'
        # The TRADING_SID from totp_validate is often stored as the internal 'edit_sid'
        client.configuration.edit_token = session_data.get("TRADING_TOKEN") 
        client.configuration.edit_sid = session_data.get("TRADING_SID") 
        client.configuration.base_url = session_data.get("BASE_URL")
        
        # 3. Handle potential property name mismatch (if client uses 'bearer_token' internally)
        # Check if the NeoAPI client needs the TRADING_TOKEN stored as 'bearer_token'
        client.configuration.bearer_token = session_data.get("TRADING_TOKEN")
        
        await redis_client.expire(redis_key, EIGHTEEN_HOURS_IN_SECONDS)
        
        return client
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recreate client from session: {e}")
    

 

