from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from base import Base

DATABASE_URL = "sqlite:///./user.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Checks for last 5 moods
def get_latest_moods(user_id: int, db: Session, n: int = 5):
    from models import ChatHistory
    return (db.query(ChatHistory.mood)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.timestamp.desc())
        .limit(n)
        .all())

# Pick the dominant mood from the past 5 moods
def update_dominant_mood(user_id: int, dominant_mood: str, db: Session):
    from models import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id, dominant_mood=dominant_mood)
        db.add(profile)
    else:
        profile.dominant_mood = dominant_mood
    db.commit()
def get_chat_history(user_id: int, db: Session, n: int = 5):
    from models import ChatHistory
    return (
        db.query(ChatHistory.message, ChatHistory.mood, ChatHistory.timestamp)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.timestamp.desc())
        .limit(n)
        .all()
    )
