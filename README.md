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

## Set up your environment:

Create a .env file in the root directory

Add your OpenAI key:

OPENAI_API_KEY=your_openai_key_here
SECRET_KEY=your_secret_key_here  

## Workflow:

1.User Registration/Login:

 -> Create account with email/password

 -> Authenticate with JWT token

2.Conversation Initiation:

 ->Start chat session

 ->System initializes mood tracking

3.Message Interaction:

 ->Send mental health-related messages

 ->System analyzes sentiment (Happy/Neutral/Sad)

 ->Responses adapt to detected mood and history

4.Session Review:

 ->View conversation history with mood timeline

 ->Access vector database entries

 ->Manage chat configurations

## Example Prompt Flow:

User: “I'm feeling overwhelmed with exams.”

System detects: mood = sad, topic = exams

Response is enhanced with mood + topic history.

System returns a short, contextual answer with “thanks for asking!” at the end.

## Screenshot:

Sign up/Log in page:
![Capture](https://github.com/user-attachments/assets/0d5bf911-2402-420a-a2dc-fcc8a1111daa)

Chatting in with the bot:
![image](https://github.com/user-attachments/assets/cd4ded85-796f-4002-a60c-a1699bc87012)

Bot remembering about previous conversations and our mood:
![image](https://github.com/user-attachments/assets/b6825565-fe01-4bb4-a6c2-266cebfcc5a2)

