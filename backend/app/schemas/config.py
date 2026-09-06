from pydantic import BaseModel
from typing import List, Optional
from app.schemas.cisco import VerifyCheck

class ConfigPlanRequest(BaseModel):
    device_id: str
    commands: List[str]
    verify: List[VerifyCheck] = []
    save_on_success: bool = False
    description: Optional[str] = None

class ConfigApplyRequest(BaseModel):
    plan_id: str
    approved_by: str

class ConfigRollbackRequest(BaseModel):
    device_id: str
    backup_id: Optional[str] = None
    plan_id: Optional[str] = None
