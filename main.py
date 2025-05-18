from dotenv import load_dotenv
load_dotenv()  # Must be FIRST import

import os
from fastapi import FastAPI
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from database import engine
from base import Base
from auth import router as auth_router
from chat import router as chat_router

# Create app FIRST
app = FastAPI()

def load_existing_vectors():
    """Load all Chroma vector stores on startup"""
    embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
    chroma_dir = "chroma_db"
    
    if os.path.exists(chroma_dir):
        print("\n=== Loading existing vector stores ===")
        for user_dir in os.listdir(chroma_dir):
            if user_dir.startswith("user_"):
                user_id = user_dir.split("_")[-1]
                Chroma(
                    collection_name=f"user_{user_id}",
                    persist_directory=os.path.join(chroma_dir, user_dir),
                    embedding_function=embeddings
                )
                print(f"Loaded vectors for user {user_id}")

@app.on_event("startup")  # Now AFTER app is defined
async def startup_event():
    # Load existing Chroma collections
    load_existing_vectors()
    
    # Verify OpenAI connection
    print("\n=== Testing OpenAI API Key Permissions ===")
    from openai import OpenAI
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        models = client.models.list()
        print(f"Successfully accessed {len(models.data)} OpenAI models")
    except Exception as e:
        print(f"OpenAI connection error: {str(e)}")
        raise

    # Create database tables
    Base.metadata.create_all(bind=engine)

# Include routers AFTER app creation
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
def read_root():
    return {"message": "Mental Health Chat API"}