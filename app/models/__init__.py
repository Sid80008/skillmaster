# Models package – all ORM models imported here for Alembic auto-detection.
from app.models.user import User, UserConstraints  # noqa: F401
from app.models.catalog import Category, ActivityFamily, Characteristic, Skill, SkillCharacteristic, SkillRelationship  # noqa: F401
from app.models.quest import Quest, QuestAttempt  # noqa: F401
from app.models.recommendation import Recommendation, RecommendationCandidate  # noqa: F401
from app.models.feedback import Feedback  # noqa: F401
