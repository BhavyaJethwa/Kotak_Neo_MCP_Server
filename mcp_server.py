from mcp.server.fastmcp import FastMCP
from fastapi import HTTPException
import httpx
import json
mcp = FastMCP("Kotak-MCP-Server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
async def get_holdings():
    """ Gets the current holding of the client"""
    NEO_WORKER_URL = "http://127.0.0.1:8001/worker/holdings"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NEO_WORKER_URL}/2c5f8ebf-1ade-4746-bded-c4502a9f5d2e")
            response.raise_for_status()
            response = response.json()
            required_keys = [
    "instrumentName", "quantity", "averagePrice",
    "holdingCost", "closingPrice", "unrealisedGainLoss"
]

            output = {
                "message": response.get("message", ""),
                "holdings": []
            }

            for item in response.get("holdings", {}).get("data", []):
                filtered = {key: item.get(key) for key in required_keys}
                output["holdings"].append(filtered)

            # ---- Result ----
            result = json.dumps(output)
            return result
        
        except httpx.HTTPStatusError as e:
            error_detail = "unknown error"
            try:
                error_detail = e.response.json().get('detail', 'unknown error')
            except:
                error_detail = str(e)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"worker error: {error_detail}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Cannot connect to Neo Worker service: {e}")

@mcp.tool()
async def get_limits():
    """ Gets the limits of the client"""
    NEO_WORKER_URL = "http://127.0.0.1:8001/worker/limits"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NEO_WORKER_URL}/2c5f8ebf-1ade-4746-bded-c4502a9f5d2e")
            response.raise_for_status()
            response = response.json()
            return response
        
        except httpx.HTTPStatusError as e:
            error_detail = "unknown error"
            try:
                error_detail = e.response.json().get('detail', 'unknown error')
            except:
                error_detail = str(e)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"worker error: {error_detail}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Cannot connect to Neo Worker service: {e}")
            
@mcp.tool()
async def get_positions():
    """ Gets the position of the client"""
    NEO_WORKER_URL = "http://127.0.0.1:8001/worker/positions"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{NEO_WORKER_URL}/2c5f8ebf-1ade-4746-bded-c4502a9f5d2e")
            response.raise_for_status()
            response = response.json()
            return response
        
        except httpx.HTTPStatusError as e:
            error_detail = "unknown error"
            try:
                error_detail = e.response.json().get('detail', 'unknown error')
            except:
                error_detail = str(e)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"worker error: {error_detail}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Cannot connect to Neo Worker service: {e}")
            
@mcp.tool()
async def buy_order(qty:str,stock:str):
    """
    Places BUY Order for the client via the local worker service.
    Parameters:
      - session_id: str
      - qty: int (>0)
      - stock: str (e.g. "SUZLON","IDEA","GRSE","HAL","BDL") stock will always be in all capital letters.
    Returns parsed JSON response from the worker (or raises an exception).
    """
    
    NEO_WORKER_URL = "http://127.0.0.1:8001/worker/buy/2c5f8ebf-1ade-4746-bded-c4502a9f5d2e"
    
    payload = {"qty": qty,
               "stock": stock}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(NEO_WORKER_URL, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = "unknown error"
            try:
                error_detail = e.response.json().get('detail', 'unknown error')
            except:
                error_detail = str(e)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"worker error: {error_detail}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Cannot connect to Neo Worker service: {e}")

@mcp.tool()
async def sell_order(qty:str,stock:str):
    """
    Places SELL Order for the client via the local worker service.
    Parameters:
      - session_id: str
      - qty: int (>0)
      - stock: str (e.g. "SUZLON","IDEA","GRSE","HAL","BDL") stock will always be in all capital letters.
    Returns parsed JSON response from the worker (or raises an exception).
    """
    
    NEO_WORKER_URL = "http://127.0.0.1:8001/worker/sell/2c5f8ebf-1ade-4746-bded-c4502a9f5d2e"
    
    payload = {"qty": qty,
               "stock": stock}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(NEO_WORKER_URL, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = "unknown error"
            try:
                error_detail = e.response.json().get('detail', 'unknown error')
            except:
                error_detail = str(e)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"worker error: {error_detail}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503, 
                detail=f"Cannot connect to Neo Worker service: {e}")
         


def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()