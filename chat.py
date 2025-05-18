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
from database import get_db, get_latest_moods, update_dominant_mood, get_chat_history
import models

router = APIRouter()

user_memories = {}
openai_api_key = os.getenv("OPENAI_API_KEY")

# Custom prompt template with context and mood integration
prompt_template = """[Retrieved Context]
{context}

[User Profile]
[User has been feeling {dominant_mood} recently and just said: “{last_message}” (mood: {last_mood})]

Current Query: {question}
Assistant:"""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "dominant_mood", "chat_history", "last_message", "last_mood", "question"]
)

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

        # Update dominant mood
        latest_moods = [m[0] for m in get_latest_moods(user.id, db)]
        dominant_mood = max(set(latest_moods), key=latest_moods.count) if latest_moods else "neutral"
        update_dominant_mood(user.id, dominant_mood, db)

        # Chroma vectorstore setup
        persist_dir = f"chroma_db/user_{user.id}"
        embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        
        vectorstore = Chroma(
            collection_name=f"user_{user.id}",
            persist_directory=persist_dir,
            embedding_function=embeddings
        )

        # Add message with metadata
        vectorstore.add_texts(
            texts=[user_input.message],
            metadatas=[{
                "mood": mood,
                "dominant_mood": dominant_mood,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": str(user.id),
                "message": user_input.message
            }]
        )

        # Get formatted chat history
        chat_history = get_chat_history(user.id, db, n=5)
        formatted_history = "\n".join(
            [f"{msg.timestamp}: {msg.message} (Mood: {msg.mood})" 
             for msg in reversed(chat_history)]
        )

        # Get last interaction details
        last_message = chat_history[0].message if chat_history else "N/A"
        last_mood = chat_history[0].mood if chat_history else "neutral"

        # Initialize AI components
        llm = ChatOpenAI(api_key=openai_api_key, temperature=0.7)
        memory = get_user_memory(user_input.email)
        
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=ConversationBufferMemory(
                memory_key="chat_history",
                input_key="question",
                return_messages=True
            ),
            verbose=True,
            combine_docs_chain_kwargs={"prompt": PROMPT},
            get_chat_history=lambda h: h
        )

        # Generate response
        result = qa_chain({
            "question": user_input.message,
            "dominant_mood": dominant_mood,
            "chat_history": formatted_history,
            "last_message": last_message,
            "last_mood": last_mood
        })

        return {
            "reply": result["answer"],
            "your_mood": mood,
            "dominant_mood": dominant_mood
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing error: {str(e)}"
        )