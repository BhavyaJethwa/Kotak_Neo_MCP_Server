from fastapi import APIRouter, HTTPException
import httpx

NEO_WORKER_URL = "http://neo-worker:8001/worker/holdings"

router = APIRouter(prefix="/holdings", tags=["auth"])

@router.get("/get-holdings")
async def get_holdings_data(session_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NEO_WORKER_URL}/{session_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                details = f"worker error {e.response.json().get('details', 'unknown error')}"
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Cannot connect to Neo Worker service: {e}")