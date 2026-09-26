from pydantic import BaseModel
import uuid
from decimal import Decimal
from datetime import datetime

class SkillDNAResponse(BaseModel):
    characteristic_slug: str
    affinity_value: Decimal
    confidence: Decimal
    sample_count: int
    last_updated_at: datetime
    
    model_config = {"from_attributes": True}

class UserCategoryProfileResponse(BaseModel):
    category_id: uuid.UUID
    category_name: str | None = None
    exposure_count: int
    affinity_score: Decimal
    fatigue_level: Decimal
    last_experienced_at: datetime | None
    affinity_score: Decimal
    fatigue_level: Decimal
    last_experienced_at: datetime | None
    
    model_config = {"from_attributes": True}

class UserProfileResponse(BaseModel):
    exploration_mode: str
    mix_mode_enabled: bool
    is_locked_in: bool
    
    model_config = {"from_attributes": True}
