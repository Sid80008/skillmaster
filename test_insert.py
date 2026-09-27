import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def test_db_insert():
    db = SessionLocal()
    try:
        user = User(
            username="testuser_999",
            email="test999@example.com",
            hashed_password=get_password_hash("password123")
        )
        db.add(user)
        db.commit()
        print("Success! User created with ID:", user.id)
    except Exception as e:
        print("Error during insert:", e)
    finally:
        db.close()

if __name__ == "__main__":
    test_db_insert()
