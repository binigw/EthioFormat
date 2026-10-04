from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

# ==============================================================================
# CBE BIRR INITIATION MODELS
# ==============================================================================

class InitiateCBEPaymentRequest(BaseModel):
    session_id: str = Field(..., description="Active preview session identifier")
    transaction_ref: Optional[str] = Field(None, description="Optional initial CBE Transaction Ref / TT number if known")
    student_name: Optional[str] = Field(None, description="Student full name")
    student_email: Optional[str] = Field(None, description="Student email address")
    student_phone: Optional[str] = Field(None, description="Student phone number")

class InitiateCBEPaymentResponse(BaseModel):
    status: str = "pending"
    session_id: str
    amount_expected: float
    currency: str = "ETB"
    total_pages: int
    cbe_account_number: str
    cbe_account_name: str
    pricing_breakdown: Dict[str, Any]
    instructions: str

# ==============================================================================
# USER SUBMISSION OF TRANSACTION ID
# ==============================================================================

class SubmitCBETransactionRequest(BaseModel):
    session_id: str = Field(..., description="Active session ID")
    transaction_ref: str = Field(..., description="CBE Transaction reference / ID (e.g., FT260987ABCD, TXN123456)")
    payer_name: Optional[str] = Field(None, description="Name on the CBE bank slip")
    payer_phone: Optional[str] = Field(None, description="Phone number used for CBE transfer")

class SubmitCBETransactionResponse(BaseModel):
    status: str  # 'pending', 'approved', 'failed'
    session_id: str
    transaction_ref: str
    amount_expected: float
    message: str
    download_url: Optional[str] = None
    file_name: Optional[str] = None

# ==============================================================================
# CBE EMAIL WEBHOOK MODELS
# ==============================================================================

class CBEWebhookPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    subject: Optional[str] = None
    from_email: Optional[str] = Field(None, alias="from")
    sender: Optional[str] = None
    to_email: Optional[str] = Field(None, alias="to")
    body: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    raw_content: Optional[str] = None
    message: Optional[str] = None
    # Support direct extracted fields if passed by intermediate parser
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    payer_name: Optional[str] = None

class CBEWebhookResponse(BaseModel):
    status: str
    message: str
    transaction_ref: Optional[str] = None
    amount_detected: Optional[float] = None
    matched_session_id: Optional[str] = None
    download_url: Optional[str] = None

# ==============================================================================
# TRANSACTION STATUS / POLLING MODEL
# ==============================================================================

class CheckTransactionStatusResponse(BaseModel):
    status: str  # 'pending' | 'approved' | 'failed'
    session_id: str
    transaction_ref: Optional[str] = None
    amount_expected: float
    amount_paid: Optional[float] = None
    verified: bool
    download_url: Optional[str] = None
    file_name: Optional[str] = None
    message: Optional[str] = None
