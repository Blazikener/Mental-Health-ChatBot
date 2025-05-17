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
def get_latest_moods(userid: int, db: Session, n: int = 5):
    from models import ChatHistory
    return (db.query(ChatHistory.mood)
        .filter(ChatHistory.userid == userid)
        .order_by(ChatHistory.timestamp.desc())
        .limit(n)
        .all())

# Pick the dominant mood from the past 5 moods
def update_dominant_mood(userid: int, dominant_mood: str, db: Session):
    from models import UserProfile
    profile = db.query(UserProfile).filter(UserProfile.userid == userid).first()
    if not profile:
        profile = UserProfile(userid=userid, dominant_mood=dominant_mood)
        db.add(profile)
    else:
        profile.dominant_mood = dominant_mood
    db.commit()