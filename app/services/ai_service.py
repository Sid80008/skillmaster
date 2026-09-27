import json
import logging
import re
from sqlalchemy.orm import Session
from sqlalchemy import select
from google import genai
from google.genai import types

from app.core.config import get_settings
from app.models.catalog import ActivityFamily, Skill
from app.models.challenge import Challenge

logger = logging.getLogger(__name__)
settings = get_settings()

def generate_quests_for_db(db: Session, num_quests: int = 2) -> int:
    """Generates quests dynamically and inserts them into the DB."""
    if not settings.gemini_api_key:
        logger.warning("No gemini API key found, skipping AI generation.")
        return 0
        
    client = genai.Client(api_key=settings.gemini_api_key)
    
    # Get all active families
    families = db.execute(select(ActivityFamily)).scalars().all()
    if not families:
        return 0
        
    fam_str = ", ".join([f.name for f in families])
    
    prompt = f"""
    You are an expert game designer creating real-world quests.
    I need {num_quests} completely unique, fun, and realistic weekend quests.
    The quests must belong to one of these Activity Families: {fam_str}
    
    Return a JSON object matching exactly this schema:
    {{
        "quests": [
            {{
                "family_name": "Family Name",
                "title": "Actionable Quest Title (e.g. Build a Birdhouse)",
                "description": "A 1-sentence description of the overall skill.",
                "difficulty_level": 3,
                "objective": "A specific objective to complete this weekend.",
                "learn_content": "2-3 short bullet points on what to research or watch first.",
                "do_content": "3-4 step-by-step instructions on how to execute it.",
                "finish_criteria": "How do you know it is complete?",
                "estimated_duration_minutes": 120
            }}
        ]
    }}
    
    Ensure difficulty is an integer between 1 and 5.
    Ensure estimated_duration_minutes is an integer like 60, 120, 180, etc.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        data = json.loads(response.text)
    except Exception as e:
        logger.error(f"Failed to generate quests: {e}")
        return 0
        
    inserted = 0
    for q in data.get("quests", []):
        try:
            # Find family
            fam = next((f for f in families if f.name.lower() == q["family_name"].lower()), None)
            if not fam:
                fam = families[0] # Fallback
                
            skill = Skill(
                name=q["title"],
                slug=re.sub(r'[^a-z0-9]+', '-', q["title"].lower()).strip('-'),
                description=q["description"],
                activity_family_id=fam.id,
                difficulty_level=min(max(int(q.get("difficulty_level", 3)), 1), 5),
                is_active=True
            )
            db.add(skill)
            db.commit()
            
            challenge = Challenge(
                skill_id=skill.id,
                title=q["title"],
                objective=q["objective"],
                learn_content=q["learn_content"],
                do_content=q["do_content"],
                finish_criteria=q["finish_criteria"],
                estimated_duration_minutes=int(q.get("estimated_duration_minutes", 120)),
                difficulty_level=min(max(int(q.get("difficulty_level", 3)), 1), 5)
            )
            db.add(challenge)
            db.commit()
            inserted += 1
        except Exception as e:
            db.rollback()
            logger.error(f"Error inserting generated quest: {e}")
            
    return inserted
