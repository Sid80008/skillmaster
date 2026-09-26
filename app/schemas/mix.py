from pydantic import BaseModel
import uuid
from decimal import Decimal

class MixCandidateResponse(BaseModel):
    id: uuid.UUID
    skill_a_id: uuid.UUID
    skill_b_id: uuid.UUID
    result_skill_id: uuid.UUID | None
    mix_label: str
    mix_explanation: str | None
    confidence: Decimal
    is_presented: bool
    
    model_config = {"from_attributes": True}
