from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", summary="Basic health check")
async def health_check():
    """
    Basic health check endpoint.
    Returns OK status and timestamp.
    Use for readiness/liveness probes.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "NEO-trading-mcp-backend"
    }
    
