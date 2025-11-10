from fastapi import APIRouter, HTTPException
from neo_api_client import NeoAPI
from app.api.utils import get_current_client, get_redis

router = APIRouter(prefix="/holdings", tags=["auth"])

redis_client = get_redis()

@router.get("/get-holdings")
async def get_holdings_data(session_id):
    try:
        client = await get_current_client(session_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Cannot get client {e}")
    
    try:
        holdings = client.holdings()
        return {"session_id": session_id, "message": "Holdings fetched", "holdings":holdings}
    except Exception as e:
        print("Exception when calling Holdings->holdings: %s\n" % e)
