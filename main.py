# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
import models
from starlette.requests import Request  
from starlette.responses import JSONResponse
from auth import router as auth_router
from chat import router as chat_router
from fastapi.responses import FileResponse
from dotenv import load_dotenv
load_dotenv()  
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import JSONResponse, FileResponse
from database import engine, Base
from auth import router as auth_router
from chat import router as chat_router
import models

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
        
    if request.url.path == "/" or \
       request.url.path.startswith("/auth") or \
       request.url.path.startswith("/static"):
        return await call_next(request)
        
    if "Authorization" not in request.headers:
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing authorization token"},
        )
    
    return await call_next(request)

# routers
app.include_router(auth_router)
app.include_router(chat_router)

# static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")