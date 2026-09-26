from pydantic import BaseModel


class ExplorationStateResponse(BaseModel):
    total_completed: int
    total_abandoned: int
    explored_families_count: int
    unexplored_categories: list[str]
    current_exploration_mode: str
    is_locked_in: bool
