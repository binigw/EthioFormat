import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load from backend/.env or root .env
root_env = Path(__file__).parent.parent.parent / ".env"
backend_env = Path(__file__).parent.parent / ".env"

if backend_env.exists():
    load_dotenv(backend_env)
elif root_env.exists():
    load_dotenv(root_env)
else:
    load_dotenv()

class Settings(BaseModel):
    APP_NAME: str = "EthioFormat API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Pricing configuration (ETB) - 50 ETB base up to 20 pages + 1.50 ETB / extra page
    BASE_PAGE_THRESHOLD: int = int(os.getenv("BASE_PAGE_THRESHOLD", "20"))
    BASE_FEE_ETB: float = float(os.getenv("BASE_FEE_ETB", "50.0"))
    INCREMENTAL_PER_PAGE_FEE_ETB: float = float(os.getenv("INCREMENTAL_PER_PAGE_FEE_ETB", "1.50"))
    
    # CBE Birr Account Details for Direct Bank Transfers
    CBE_ACCOUNT_NUMBER: str = os.getenv("CBE_ACCOUNT_NUMBER", "1000123456789")
    CBE_ACCOUNT_NAME: str = os.getenv("CBE_ACCOUNT_NAME", "EthioFormat / Thesis Automation Services")
    CBE_WEBHOOK_SECRET: str = os.getenv("CBE_WEBHOOK_SECRET", "")
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_BUCKET_NAME: str = os.getenv("SUPABASE_BUCKET_NAME", "ethioformat-documents")
    
    # Local Storage Staging Path (for encrypted/secure session holding)
    STORAGE_STAGING_DIR: str = os.getenv("STORAGE_STAGING_DIR", "/home/user/backend/storage_temp")
    
    # Temporary signed link validity
    SIGNED_URL_EXPIRY_HOURS: int = int(os.getenv("SIGNED_URL_EXPIRY_HOURS", "24"))

settings = Settings()
