from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class InitiatePaymentRequest(BaseModel):
    session_id: str
    email: str = Field(..., description="Student email address")
    first_name: str = Field(..., description="Student first name")
    last_name: str = Field(..., description="Student last name")
    phone_number: Optional[str] = Field(None, description="Student Ethiopian phone number (e.g. 0911223344)")

class InitiatePaymentResponse(BaseModel):
    status: str
    checkout_url: str
    tx_ref: str
    amount: float
    currency: str = "ETB"
    session_id: str

class VerifyPaymentRequest(BaseModel):
    tx_ref: str
    session_id: str

class VerifyPaymentResponse(BaseModel):
    status: str
    verified: bool
    download_url: Optional[str] = None
    expires_in_hours: Optional[int] = 24
    file_name: Optional[str] = None
    error: Optional[str] = None
