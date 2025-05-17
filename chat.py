from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from textblob import TextBlob
from datetime import datetime
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
import os
import schemas
from database import get_db, get_latest_moods, update_dominant_mood
import models

router = APIRouter()

user_memories = {}
openai_api_key = os.getenv("OPENAI_API_KEY")

def get_user_memory(user_id: str):
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return user_memories[user_id]

@router.post("/chat", response_model=schemas.ChatOut)
def chat(user_input: schemas.ChatInput, db: Session = Depends(get_db)):
    try:
        # User verification
        user = db.query(models.User).filter(models.User.email == user_input.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        # Sentiment analysis
        polarity = TextBlob(user_input.message).sentiment.polarity
        mood = "happy" if polarity > 0.2 else "sad" if polarity < -0.2 else "neutral"

        # Store chat history
        chat_entry = models.ChatHistory(
            user_id=user.id,
            message=user_input.message,
            mood=mood
        )
        db.add(chat_entry)
        db.commit()

        # Initialize AI components
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        vectorstore = Chroma(collection_name=f"user_{user.id}",
                             persist_directory="chroma_db", embedding_function=embeddings)
        vectorstore.persist() 
        llm = ChatOpenAI(api_key=openai_api_key, temperature=0.7)
        memory = get_user_memory(user_input.email)
        
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=memory
        )

        # Get AI response
        result = qa_chain.invoke({"question": user_input.message})
        response = result["answer"]

        # Updateds mood profile
        latest_moods = [m[0] for m in get_latest_moods(user.id, db)]
        dominant_mood = max(set(latest_moods), key=latest_moods.count) if latest_moods else "neutral"
        update_dominant_mood(user.id, dominant_mood, db)

        return {"reply": response,}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing error: {str(e)}"
        )
