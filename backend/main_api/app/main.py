from fastapi import FastAPI
from app.api import health
from app.api import validate
from app.api import holdings

app = FastAPI(title="Trading MCP API", version="1.0.0")

# Routers
app.include_router(health.router)
app.include_router(validate.router)
app.include_router(holdings.router)


@app.get("/")
async def root():
    return {"message": "Trading MCP backend running"}
