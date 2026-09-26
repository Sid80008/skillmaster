import uuid

from pydantic import BaseModel


class ChallengeResponse(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    title: str
    subtitle: str | None
    objective: str
    learn_content: str | None
    do_content: str
    finish_criteria: str
    stretch_goal: str | None
    why_this_matters: str | None
    resources: str | None
    estimated_duration_minutes: int
    difficulty_level: int
    
    model_config = {"from_attributes": True}
