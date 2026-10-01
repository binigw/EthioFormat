import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.models.presets import PresetsListResponse

router = APIRouter(prefix="/api/presets", tags=["presets"])

DATA_FILE = Path(__file__).parent.parent / "data" / "university_presets.json"

@router.get("", response_model=PresetsListResponse)
def get_presets():
    """Returns all 22 Ethiopian university presets plus custom mode configurations."""
    if not DATA_FILE.exists():
        raise HTTPException(status_code=500, detail="Presets configuration file not found")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
