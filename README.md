# Mental Health Chatbot
This is an interactive conversational interface that enables users to chat with their own data (PDFs). Built using Python, Panel, and LangChain, the bot keeps track of conversation history, detects user mood, extracts discussed topics, and enhances responses using Retrieval-Augmented Generation (RAG) over documents like lecture notes.

## Features
Mood Detection - Real-time sentiment analysis using TextBlob

Persistent Memory - Stores conversations with ChromaDB vector embeddings

Secure Authentication - JWT-based user registration/login

Contextual Responses - Retrieval-Augmented Generation (RAG) for personalized answers

Docker Support - Containerized deployment with persistent storage

Clone the repository:
```bash
git clone https://github.com/Blazikener/mental-health-chatbot.git
cd mental-health-chatbot
```

## Install dependencies:

```bash
pip install -r requirements.txt
```
