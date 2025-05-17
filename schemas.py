from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatInput(BaseModel):
    email: EmailStr
    message: str

class ChatOut(BaseModel):
    reply: str
    your_mood: str
    dominant_mood: str

    class Config:
        from_attributes = True