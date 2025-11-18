from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict
import httpx
from pydantic import BaseModel, Field
import json

class ValidateRequest(BaseModel):
    totp: str = Field(..., min_length=4, max_length=32)
    consumer_key: str
    mobile_number: str
    ucc: str
    mpin: str

NEO_WORKER_URL = "http://neo-worker:8001/worker/validate/"

router = APIRouter(prefix="/validate", tags=["auth"])


@router.post("")
async def validate(req: ValidateRequest):
    async with httpx.AsyncClient() as client:
        try: 
            response = await client.post(f"{NEO_WORKER_URL}", json=req.dict())
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            try:
                worker_error_body = e.response.json()
                worker_detail = worker_error_body.get('detail','Worker service returned error status without detail.')
            except json.JSONDecodeError:
                worker_detail = f"Worker service returned status {e.response.status_code} with non-JSON body: {e.response.text[:100]}..."
            
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Worker authentication error: {worker_detail}"
            )
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Cannot connect to Neo Worker service: {e}")