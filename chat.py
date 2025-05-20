# chat.py (updated)
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
from auth import get_current_user
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Validate OpenAI API Key
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable not set")

openai_api_key = os.getenv("OPENAI_API_KEY")
embeddings = OpenAIEmbeddings(api_key=openai_api_key)

# Enhanced prompt template with mood context
prompt_template = """Use the following context and chat history to answer the question. 
Consider the user's emotional state in your response.

[User Mood Context]
Dominant Mood: {dominant_mood}
Last Interaction Mood: {last_mood}

[Context]
{context}

[Chat History]
{chat_history}

[Question]
{question}

[Response]
"""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question", "chat_history", "dominant_mood", "last_mood"]
)

def get_vectorstore(user_id: str):
    persist_dir = f"chroma_db/user_{user_id}"
    return Chroma(
        collection_name=f"user_{user_id}",
        persist_directory=persist_dir,
        embedding_function=embeddings
    )

@router.post("/chat", response_model=schemas.ChatOut)
def chat(
    user_input: schemas.ChatInput, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    try:
        user = current_user

        # Sentiment analysis
        blob = TextBlob(user_input.message)
        polarity = blob.sentiment.polarity
        current_mood = "happy" if polarity > 0.2 else "sad" if polarity < -0.2 else "neutral"

        # Store chat history
        chat_entry = models.ChatHistory(
            user_id=user.id,
            message=user_input.message,
            mood=current_mood
        )
        db.add(chat_entry)
        db.commit()

        # Update dominant mood
        latest_moods = [m[0] for m in get_latest_moods(user.id, db)]
        dominant_mood = max(set(latest_moods), key=latest_moods.count) if latest_moods else "neutral"
        update_dominant_mood(user.id, dominant_mood, db)

        # Chroma vectorstore operations
        vectorstore = get_vectorstore(user.id)
        
        # Add to vectorstore with metadata
        vectorstore.add_texts(
            texts=[user_input.message],
            metadatas=[{
                "user_id": str(user.id),
                "timestamp": datetime.utcnow().isoformat(),
                "mood": current_mood,
                "dominant_mood": dominant_mood,
                "type": "user_message"
            }]
        )

        # Get historical context
        chat_history = get_chat_history(user.id, db, n=5)
        last_mood = chat_history[0].mood if chat_history else "neutral"

        # Initialize conversation chain
        llm = ChatOpenAI(api_key=openai_api_key, temperature=0.7)
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            output_key="answer"
        )
        
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
            memory=memory,
            verbose=True,
            combine_docs_chain_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )

        # Prepare chain inputs with required parameters
        chain_inputs = {
            "question": user_input.message,
            "chat_history": [f"{msg.message} (Mood: {msg.mood})" for msg in chat_history],
            "dominant_mood": dominant_mood,
            "last_mood": last_mood
        }

        # Generate response
        result = qa_chain.invoke(chain_inputs)

        return {
            "reply": result["answer"],
            "your_mood": current_mood,
            "dominant_mood": dominant_mood
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing error: {str(e)}"
        )