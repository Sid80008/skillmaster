import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.models.catalog import Category, ActivityFamily, Skill
from app.models.user import UserConstraints

def override_get_db(db: Session):
    def _override():
        yield db
    return _override

@pytest.fixture
def auth_client(db: Session):
    app.dependency_overrides[get_db] = override_get_db(db)
    client = TestClient(app)
    import uuid
    uid = uuid.uuid4().hex[:8]
    # Setup some basic catalog data so recommendations work
    cat = Category(name=f"Creative_{uid}", slug=f"creative-{uid}")
    db.add(cat)
    db.flush()
    fam = ActivityFamily(name=f"Photography_{uid}", slug=f"photography-{uid}", category_id=cat.id)
    db.add(fam)
    db.flush()
    skill = Skill(
        name=f"Phone Street Photography {uid}", 
        slug=f"phone-street-{uid}", 
        activity_family_id=fam.id, 
        is_active=True,
        characteristic_tags="creative,visual"
    )
    db.add(skill)
    db.flush()

    email = f"test_{uid}@example.com"
    # Create user directly
    from app.models.user import User
    from app.core.security import create_access_token
    user = User(email=email, username=f"testuser_{uid}", hashed_password="fake_hashed_password")
    db.add(user)
    db.flush()
    db.refresh(user)

    token = create_access_token(str(user.id))
    yield TestClient(app, headers={"Authorization": f"Bearer {token}"})

def test_unauthenticated_rejected():
    client = TestClient(app)
    response = client.get("/api/v1/profile")
    assert response.status_code == 401

def test_end_to_end_exploration_cycle(auth_client):
    # 1. Generate Recommendation
    res = auth_client.post("/api/v1/recommendations/")
    assert res.status_code == 201
    rec = res.json()
    rec_id = rec["id"]
    
    # 2. Check candidates
    assert len(rec["candidates"]) > 0
    candidate = rec["candidates"][0]
    skill_id = candidate["skill_id"]
    
    # 3. Present and Accept
    auth_client.post(f"/api/v1/recommendations/{rec_id}/present")
    res = auth_client.post(f"/api/v1/recommendations/{rec_id}/accept", json={"selected_skill_id": skill_id})
    assert res.status_code == 201
    attempt = res.json()
    attempt_id = attempt["id"]
    
    # Check /current quest
    res = auth_client.get("/api/v1/quests/current")
    assert res.status_code == 200
    assert res.json()["id"] == attempt_id
    
    # Check challenge
    res = auth_client.get(f"/api/v1/quests/attempts/{attempt_id}/challenge")
    assert res.status_code in (200, 404) # 404 if challenge wasn't created in setup
    
    # 4. Start Quest
    res = auth_client.post(f"/api/v1/quests/attempts/{attempt_id}/start")
    assert res.status_code == 200
    assert res.json()["status"] == "active"
    
    # 5. Complete Quest
    res = auth_client.post(f"/api/v1/quests/attempts/{attempt_id}/complete")
    assert res.status_code == 200
    assert res.json()["status"] == "completed"
    
    # 6. Submit feedback
    res = auth_client.post(f"/api/v1/quests/attempts/{attempt_id}/feedback", json={
        "enjoyment": 9,
        "curiosity": 8,
        "deep_dive_interest": 7,
        "would_repeat": "yes",
        "pre_interest": 5,
        "difficulty_felt": 4
    })
    assert res.status_code == 201
    rating = res.json()
    assert rating["composite_score"] is not None
    
    # 7. Fetch DNA / Profile
    res = auth_client.get("/api/v1/profile/dna")
    assert res.status_code == 200
    dna = res.json()
    assert len(dna) > 0 # Should have extracted "creative" and "visual"
    
    res = auth_client.get("/api/v1/profile/categories")
    assert res.status_code == 200
    assert len(res.json()) > 0
    
    res = auth_client.get("/api/v1/exploration/")
    assert res.status_code == 200
    assert res.json()["total_completed"] == 1
    
    # 8. Generate next recommendation (should have fatigue applied)
    res = auth_client.post("/api/v1/recommendations/")
    assert res.status_code == 404
    
def test_lockin_lifecycle(auth_client):
    # Need a skill to lock in
    res = auth_client.post("/api/v1/recommendations/")
    skill_id = res.json()["candidates"][0]["skill_id"]
    
    # Activate
    res = auth_client.post("/api/v1/lock-in/activate", json={"skill_id": skill_id})
    assert res.status_code == 201
    assert res.json()["status"] == "active"
    
    # Duplicate fails
    res = auth_client.post("/api/v1/lock-in/activate", json={"skill_id": skill_id})
    assert res.status_code == 409
    
    # Current
    res = auth_client.get("/api/v1/lock-in/current")
    assert res.status_code == 200
    assert res.json()["status"] == "active"
    
    # Exit
    res = auth_client.post("/api/v1/lock-in/exit", json={"reason": "done"})
    assert res.status_code == 200
    assert res.json()["status"] == "unlocked"

def test_mix_candidates_forbidden_if_disabled(auth_client):
    res = auth_client.get("/api/v1/mix/candidates")
    # Mix mode is disabled by default
    assert res.status_code == 403
