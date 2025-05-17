from fastapi import FastAPI
import os   
from database import engine
from base import Base
from openai import OpenAI
from auth import router as auth_router
from chat import router as chat_router
from dotenv import load_dotenv

load_dotenv()
print("\n=== Testing OpenAI API Key Permissions ===")
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    models = client.models.list()
    print("Successfully accessed", len(models.data), "models")
except Exception as e:
    print("Permission Error:", str(e))
    raise SystemExit("Stopping server due to OpenAI configuration issues")

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
def read_root():
    return {"message": "Mental Health Chat API"}