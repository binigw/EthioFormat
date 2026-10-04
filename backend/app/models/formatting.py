from typing import List, Optional
from pydantic import BaseModel, Field

class CustomRulesInput(BaseModel):
    font_family: str = Field(default="Times New Roman", description="Times New Roman | Arial")
    font_size: int = Field(default=12, description="12 | 11")
    line_spacing: float = Field(default=1.5, description="1.5 | 2.0 | 1.0")
    margin_preset: str = Field(default="ethiopian_standard", description="ethiopian_standard | equal_margins")
    toc_mode: str = Field(default="auto_generate", description="auto_generate | keep_existing")

class PricingDetailModel(BaseModel):
    base_fee: float = 50.0
    incremental_fee: float = 0.0
    total_fee: float = 50.0
    currency: str = "ETB"

class PreviewMetadataModel(BaseModel):
    filename: str
    formatted_at: str
    university: str
    preset_id: str

class PreviewResponseModel(BaseModel):
    status: str = "success"
    session_id: str
    total_pages: int
    preview_pages: List[str]  # Base64 data URLs for pages 1, 2, 3
    pricing: PricingDetailModel
    cbe_account_number: str = "1000123456789"
    cbe_account_name: str = "EthioFormat / Thesis Automation Services"
    metadata: PreviewMetadataModel
    error_message: Optional[str] = None
