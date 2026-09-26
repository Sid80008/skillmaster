from pydantic import BaseModel
import uuid
from datetime import datetime

class LockInActivateRequest(BaseModel):
    skill_id: uuid.UUID

class LockInSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    skill_id: uuid.UUID
    status: str
    progression_level: int
    started_at: datetime
    ended_at: datetime | None
    unlock_reason: str | None
    
    model_config = {"from_attributes": True}
