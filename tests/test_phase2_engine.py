import pytest
from app.services.rating_service import submit_rating
from app.services.recommendation_service import _generate_candidates
from app.services.history_service import get_exploration_summary
from app.models.dna import UserCategoryProfile, SkillDNA
from tests.conftest import make_user, make_category, make_family, make_skill, make_quest, make_attempt

def test_rating_submission_updates_fatigue_and_dna(db):
    user = make_user(db)
    cat = make_category(db)
    fam = make_family(db, category=cat)
    skill = make_skill(db, family=fam, characteristic_tags="creative,visual")
    quest = make_quest(db, skill=skill)
    attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="completed")
    
    db.flush()
    
    rating = submit_rating(
        db=db,
        user=user,
        attempt_id=attempt.id,
        enjoyment=9,
        curiosity=8,
        would_repeat="yes",
        deep_dive_interest=7,
    )
    
    assert rating.composite_score is not None
    assert rating.composite_score > 0
    
    # Check fatigue was updated
    ucp = db.query(UserCategoryProfile).filter_by(user_id=user.id, category_id=cat.id).first()
    assert ucp is not None
    assert float(ucp.fatigue_level) == 0.2
    assert ucp.exposure_count == 1
    
    # Check DNA was updated
    dna = db.query(SkillDNA).filter_by(user_id=user.id).all()
    assert len(dna) == 2
    tags = {d.characteristic_slug for d in dna}
    assert tags == {"creative", "visual"}
    
def test_fatigue_penalizes_recommendations(db):
    user = make_user(db)
    cat = make_category(db)
    fam = make_family(db, category=cat)
    
    # Skill 1 is experienced
    skill1 = make_skill(db, family=fam)
    quest1 = make_quest(db, skill=skill1)
    attempt1 = make_attempt(db, user=user, skill=skill1, quest=quest1, status="completed")
    
    # Simulate a rating giving fatigue
    submit_rating(
        db=db,
        user=user,
        attempt_id=attempt1.id,
        enjoyment=5,
        curiosity=5,
        would_repeat="no",
        deep_dive_interest=1,
    )
    
    # Skill 2 is in same family
    skill2 = make_skill(db, family=fam)
    
    # Skill 3 is completely new category
    cat3 = make_category(db)
    fam3 = make_family(db, category=cat3)
    skill3 = make_skill(db, family=fam3)
    
    summary = get_exploration_summary(db, user_id=user.id)
    from app.core.config import get_settings
    get_settings().recommendation_batch_size = 1000
    candidates = _generate_candidates(db, user, summary)
    
    # Skill 3 should score higher than Skill 2 because Skill 2 suffers family & category fatigue
    score2 = next(c.score for c in candidates if c.skill.id == skill2.id)
    score3 = next(c.score for c in candidates if c.skill.id == skill3.id)
    
    assert score3 > score2
