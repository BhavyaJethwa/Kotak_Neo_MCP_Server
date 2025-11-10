import json
import uuid
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict
from app.api.models import ValidateRequest
from neo_api_client import NeoAPI
import redis

# Assuming redis_client and TWELVE_HOURS_IN_SECONDS are initialized
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    EIGHTEEN_HOURS_IN_SECONDS = 18 * 60 * 60
except Exception:
    redis_client = None

router = APIRouter(prefix="/validate", tags=["auth"])


@router.post("")
async def validate(req: ValidateRequest):
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis service is unavailable.")
    
    try:
        # 1. Initialize Client (Consumer Key is passed here, but tokens are None)
        client = NeoAPI(
            environment="prod",
            access_token=None,  
            neo_fin_key=None,  
            consumer_key=req.consumer_key,
        )
        
        # --- Step 2a: TOTP Login (Get VIEW_TOKEN) ---
        # The library method is client.totp_login(), which returns the response object.
        login_response = client.totp_login(
            mobile_number=req.mobile_number, 
            ucc=req.ucc, 
            totp=req.totp
        )
        

        # --- Step 2b: MPIN Validate (Get TRADING_TOKEN) ---
        # The library handles the header construction (Auth, sid) internally based on the view tokens.
        client.totp_validate(mpin=req.mpin)

        # --- FINAL TOKEN EXTRACTION FOR REDIS STORAGE ---
        # After totp_validate, the client.configuration should hold the final TRADING tokens.
        config_vars = vars(client.configuration)
        
        TRADING_TOKEN = config_vars.get('edit_token')  # Assumed to be the TRADING_TOKEN
        TRADING_SID = config_vars.get('edit_sid')      # Assumed to be the TRADING_SID
        BASE_URL = config_vars.get('base_url')
        
        if not TRADING_TOKEN or not TRADING_SID:
            raise HTTPException(status_code=404, 
                                detail="MPIN validation succeeded, but final TRADING tokens (edit_token/edit_sid) were not found.")

        # 2. Store the essential data in Redis
        session_data = {
            # Use final trading tokens for all future API calls
            "TRADING_TOKEN": TRADING_TOKEN,
            "TRADING_SID": TRADING_SID,
            "BASE_URL": BASE_URL,
            
            # Static data
            "consumer_key": req.consumer_key,
            "environment": "prod",
            "neo_fin_key": config_vars.get('neo_fin_key') or "neotradeapi" # Default if not set
        }

        # 3. Serialize and store in Redis with 12-hour expiration
        session_data_json = json.dumps(session_data)
        session_id = str(uuid.uuid4())
        redis_key = f"session:{session_id}"
        
        redis_client.set(redis_key, session_data_json, ex=EIGHTEEN_HOURS_IN_SECONDS)

        return {"session_id": session_id, "message": "Authenticated. Trading session stored in Redis."}
    
    except Exception as e:
        # Provide a general error message, but log the full exception on the server side
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")