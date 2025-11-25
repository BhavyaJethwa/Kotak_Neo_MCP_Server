from fastapi import FastAPI, HTTPException
import redis.asyncio as aioredis
import json
from fastapi import HTTPException
from neo_api_client import NeoAPI
from pydantic import BaseModel, Field
import uuid

EIGHTEEN_HOURS_IN_SECONDS = 18 * 60 * 60

redis_connection = None

def create_redis_client():
    """Returns a client object, but does NOT connect yet."""
    return aioredis.Redis(
        host='redis', 
        port=6379, 
        db=0, 
        decode_responses=True
    )

async def get_current_client(x_session_id: str):
    
    if not global_redis_client:
        raise HTTPException(status_code=503, detail="Redis service is unavailable.")
    
    # ... (Redis fetch logic) ...
    redis_key = f"session:{x_session_id}"
    session_data_json = await global_redis_client.get(redis_key)
    
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
        
        await global_redis_client.expire(redis_key, EIGHTEEN_HOURS_IN_SECONDS)
        
        return client
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recreate client from session: {e}")
    
class ValidateRequest(BaseModel):
    totp: str = Field(..., min_length=4, max_length=32)
    consumer_key: str
    mobile_number: str
    ucc: str
    mpin: str


# -----------------------------------------------------------

global_redis_client = None

app = FastAPI(title="Koatk Neo Worker", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    global global_redis_client
    try:
        global_redis_client = create_redis_client()
        await global_redis_client.ping()
        print("Connection to Redis success")
    except Exception as e:
        print(f"FATAL: could not connect to redis: {e}")
        global_redis_client = None
        
@app.on_event("shutdown")
async def shutdown_event():
    global global_redis_client
    if global_redis_client:
        await global_redis_client.close()

@app.get("/worker/holdings/{session_id}")
async def get_holdings_data(session_id: str):
    """Fetches holdings using Koatk Neo library (websockets==8.0)."""
    try:
        client = await get_current_client(session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Cannot get client: {e}")
    
    try:
        holdings = client.holdings()
        return {"session_id": session_id, "message": "Holdings fetched", "holdings": holdings}
    except Exception as e:
        # Log the error in the worker service's logs
        print(f"Exception when calling holdings: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching holdings from Koatk Neo: {e}")
    
@app.get("/worker/limits/{session_id}")
async def get_limits_data(session_id: str):
    """Fetches limits using Koatk Neo library (websockets==8.0)."""
    try:
        client = await get_current_client(session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Cannot get client: {e}")
    
    try:
        limits = client.limits()
        return {"session_id": session_id, "message": "Holdings fetched", "limits": limits}
    except Exception as e:
        # Log the error in the worker service's logs
        print(f"Exception when calling limits: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching limits from Koatk Neo: {e}")
    
@app.get("/worker/positions/{session_id}")
async def get_positions_data(session_id: str):
    """Fetches positions using Koatk Neo library (websockets==8.0)."""
    try:
        client = await get_current_client(session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Cannot get client: {e}")
    
    try:
        positions = client.positions()
        return {"session_id": session_id, "message": "Holdings fetched", "positions": positions}
    except Exception as e:
        # Log the error in the worker service's logs
        print(f"Exception when calling positions: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching positions from Koatk Neo: {e}")
    
from pydantic import BaseModel

class BuyOrderRequest(BaseModel):
    qty: int
    stock: str
    
@app.post("/worker/buy/{session_id}")
async def buy_order(session_id:str, order_data: BuyOrderRequest):
    """ Place order to BUY stock for client """
    try:
        qty = order_data.qty
        qty = str(qty)
        stock = order_data.stock
        client = await get_current_client(session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Cannot get client: {e}")
    try:
        response = client.place_order(
        exchange_segment="nse_cm",
        product="CNC",
        price="0",
        order_type="MKT",
        quantity=qty,
        validity="DAY",
        trading_symbol= stock + "-EQ",
        transaction_type="B",
        amo="YES",
        disclosed_quantity="0",
        market_protection="0",
        pf="N",
        trigger_price="0",
        tag=None,
        scrip_token=None,
        square_off_type=None,
        stop_loss_type=None,
        stop_loss_value=None,
        square_off_value=None,
        last_traded_price=None,
        trailing_stop_loss=None,
        trailing_sl_value=None,
    )   
        print(response)
        return response
    except Exception as e:
        print("Exception when calling OrderApi->place_order: %s\n" % e)
    
class SellOrderRequest(BaseModel):
    qty: int
    stock: str
    
@app.post("/worker/sell/{session_id}")
async def sell_order(session_id:str, order_data: SellOrderRequest):
    """ Place order to SELL stock for client """
    try:
        qty = order_data.qty
        qty = str(qty)
        stock = order_data.stock
        client = await get_current_client(session_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Cannot get client: {e}")
    try:
        response = client.place_order(
        exchange_segment="nse_cm",
        product="CNC",
        price="0",
        order_type="MKT",
        quantity=qty,
        validity="DAY",
        trading_symbol= stock + "-EQ",
        transaction_type="S",
        amo="YES",
        disclosed_quantity="0",
        market_protection="0",
        pf="N",
        trigger_price="0",
        tag=None,
        scrip_token=None,
        square_off_type=None,
        stop_loss_type=None,
        stop_loss_value=None,
        square_off_value=None,
        last_traded_price=None,
        trailing_stop_loss=None,
        trailing_sl_value=None,
    )   
        print(response)
        return response
    except Exception as e:
        print("Exception when calling OrderApi->place_order: %s\n" % e)


@app.post("/worker/validate/")    
async def validate(req: ValidateRequest):
    if not global_redis_client:
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
        
        await global_redis_client.set(redis_key, session_data_json, ex=EIGHTEEN_HOURS_IN_SECONDS)

        return {"session_id": session_id, "message": "Authenticated. Trading session stored in Redis."}
    
    except Exception as e:
        # Provide a general error message, but log the full exception on the server side
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")