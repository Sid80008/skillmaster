"""
Seed script for the Skill Quest catalog.

Populates categories, families, skills, and challenges.
"""
import sys
import uuid
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.catalog import Category, ActivityFamily, Skill
from app.models.challenge import Challenge

# Data from spec
CATEGORIES = {
    "CREATIVE": ["Drawing", "Painting", "Photography", "Film", "Animation", "3D", "Craft", "Writing"],
    "TECHNICAL": ["Programming", "Electronics", "Robotics", "CAD", "Data", "AI", "Engineering"],
    "PRACTICAL": ["Cooking", "Repair", "Woodworking", "Sewing", "Gardening", "DIY"],
    "PHYSICAL": ["Sports", "Skating", "Dance", "Climbing", "Martial Arts", "Fitness"],
    "INTELLECTUAL": ["Chess", "Mathematics", "Languages", "Psychology", "Logic", "Strategy"],
    "SOCIAL": ["Public Speaking", "Acting", "Debate", "Negotiation", "Teaching", "Improvisation"],
    "CULTURAL": ["Music", "History", "Art History", "Literature", "Philosophy"],
    "EXPERIMENTAL": ["Unusual crafts", "Weird science", "Novel techniques", "Cross-disciplinary"]
}

SKILLS_SEED = [
    {
        "category": "CREATIVE",
        "family": "Photography",
        "name": "Phone Street Photography",
        "slug": "phone-street-photography",
        "desc": "Tell a story using only your phone camera in your local neighborhood.",
        "difficulty_level": 2,
        "estimated_duration_minutes": 120,
        "characteristic_tags": "creative,visual,observation,outdoor",
        "skill_type": "creative",
        "challenge": {
            "title": "Neighborhood Storyteller",
            "objective": "Take 15 photographs telling a story using only your phone.",
            "do_content": "Walk around your neighborhood. Focus on lighting, shadows, and daily life. Do not use zoom.",
            "finish_criteria": "Select your best 15 photos and arrange them in sequence.",
        }
    },
    {
        "category": "TECHNICAL",
        "family": "Electronics",
        "name": "Arduino Traffic Light",
        "slug": "arduino-traffic-light",
        "desc": "Build a basic traffic-light system with LEDs and Arduino.",
        "difficulty_level": 4,
        "estimated_duration_minutes": 180,
        "characteristic_tags": "technical,hands-on,problem-solving,logic",
        "skill_type": "technical",
        "equipment_tags": "arduino_starter_kit",
        "challenge": {
            "title": "Traffic Controller",
            "objective": "Build a basic traffic-light system.",
            "do_content": "Wire 3 LEDs (Red, Yellow, Green) to your Arduino. Write code to cycle them realistically.",
            "finish_criteria": "A continuously running loop matching a real traffic light pattern.",
        }
    },
    {
        "category": "PRACTICAL",
        "family": "Cooking",
        "name": "From-Scratch Pasta",
        "slug": "from-scratch-pasta",
        "desc": "Make fresh pasta dough using only flour and eggs.",
        "difficulty_level": 3,
        "estimated_duration_minutes": 150,
        "characteristic_tags": "practical,hands-on,creative,indoor",
        "skill_type": "practical",
        "challenge": {
            "title": "The Italian Grandmother",
            "objective": "Make a single portion of fresh pasta completely from scratch.",
            "do_content": "Mix 100g flour and 1 egg. Knead for 10 mins. Rest for 30 mins. Roll it out and cut it.",
            "finish_criteria": "Cook the pasta and eat it with a simple sauce.",
        }
    }
]

def slugify(text: str) -> str:
    return text.lower().replace(" ", "-")

def seed():
    # Make sure all tables are created (for dev/sqlite)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create categories and families
        cat_map = {}
        fam_map = {}
        for cat_name, families in CATEGORIES.items():
            cat = db.query(Category).filter_by(slug=slugify(cat_name)).first()
            if not cat:
                cat = Category(name=cat_name.title(), slug=slugify(cat_name), description=f"{cat_name} skills")
                db.add(cat)
                db.flush()
            cat_map[cat_name] = cat
            
            for fam_name in families:
                fam = db.query(ActivityFamily).filter_by(slug=slugify(fam_name)).first()
                if not fam:
                    fam = ActivityFamily(name=fam_name, slug=slugify(fam_name), category_id=cat.id)
                    db.add(fam)
                    db.flush()
                fam_map[fam_name] = fam

        # Create skills
        for s in SKILLS_SEED:
            skill = db.query(Skill).filter_by(slug=s["slug"]).first()
            if not skill:
                fam = fam_map[s["family"]]
                skill = Skill(
                    name=s["name"],
                    slug=s["slug"],
                    description=s["desc"],
                    activity_family_id=fam.id,
                    difficulty_level=s["difficulty_level"],
                    estimated_duration_minutes=s["estimated_duration_minutes"],
                    characteristic_tags=s.get("characteristic_tags"),
                    skill_type=s.get("skill_type"),
                    required_equipment_tags=s.get("equipment_tags"),
                )
                db.add(skill)
                db.flush()
                
                # Create challenge
                c_data = s["challenge"]
                challenge = Challenge(
                    skill_id=skill.id,
                    title=c_data["title"],
                    objective=c_data["objective"],
                    do_content=c_data["do_content"],
                    finish_criteria=c_data["finish_criteria"],
                    difficulty_level=s["difficulty_level"],
                    estimated_duration_minutes=s["estimated_duration_minutes"]
                )
                db.add(challenge)
                
        db.commit()
        print("Catalog seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding catalog: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
