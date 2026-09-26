# Models package – all ORM models imported here for Alembic auto-detection.
from app.models.catalog import (  # noqa: F401
    ActivityFamily,
    Category,
    Characteristic,
    Skill,
    SkillCharacteristic,
    SkillRelationship,
)
from app.models.challenge import Challenge  # noqa: F401
from app.models.dna import SkillDNA, UserCategoryProfile  # noqa: F401
from app.models.feedback import Feedback  # noqa: F401
from app.models.lockin import LockInSession, MixCandidate  # noqa: F401
from app.models.quest import Quest, QuestAttempt  # noqa: F401
from app.models.rating import Rating  # noqa: F401
from app.models.recommendation import Recommendation, RecommendationCandidate  # noqa: F401
from app.models.user import User, UserConstraints  # noqa: F401
