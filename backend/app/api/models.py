from pydantic import BaseModel, Field

class ValidateRequest(BaseModel):
    totp: str = Field(..., min_length=4, max_length=32)
    consumer_key: str
    mobile_number: str
    ucc: str
    mpin: str
    
class ValidateResponse(BaseModel):
    session_id: str
    message: str