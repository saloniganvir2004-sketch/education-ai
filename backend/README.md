# Education AI Assistant Backend

## Overview

The Education AI Assistant Backend is an AI-powered educational question-answering system developed using FastAPI, PostgreSQL, Redis, OpenAI GPT-5 Nano, and AssemblyAI. The backend uses Retrieval-Augmented Generation (RAG) to generate accurate, context-aware answers from uploaded educational documents.

---

## Features

- AI-powered Question Answering
- Retrieval-Augmented Generation (RAG)
- Semantic Search using Embeddings
- Subject Management
- Topic Management
- Document Upload & Processing
- Question-Answer Repository
- Quiz Generation
- Summary Generation
- Mind Map Generation
- Audio Question Processing
- Multilingual Support
- Conversation Memory
- Response Caching
- Interactive Swagger API Documentation

---

## Technology Stack

- Python 3.13
- FastAPI
- PostgreSQL
- Redis
- SQLAlchemy
- pgvector
- OpenAI GPT-5 Nano
- OpenAI Embeddings
- AssemblyAI
- PyMuPDF
- python-docx
- Uvicorn

---

## System Requirements

- Python 3.13 (only for development)
- PostgreSQL 15+
- Redis Server
- Internet Connection
- OpenAI API Key
- AssemblyAI API Key

---

## Project Structure

backend/

├── api.py

├── launcher.py

├── config.py

├── database.py

├── models.py

├── schemas.py

├── routes/

├── services/

├── uploads/

├── static/

├── cache.py

├── qa_db.py

├── conversation.py

├── embeddings.py

├── retriever.py

├── translator.py

├── answer_generator.py

├── quiz_generator.py

├── summary_generator.py

├── mindmap_generator.py

├── requirements.txt

├── .env

├── .env.example

└── README.md

---

## PostgreSQL Setup

1. Install PostgreSQL.
2. Create a database.
3. Enable the pgvector extension.
4. Update the PostgreSQL credentials in the `.env` file.

---

## Redis Setup

1. Install Redis.
2. Start the Redis server.
3. Verify Redis is running on the configured host and port.

---

## Environment Configuration

Copy the example environment file.

```
cp .env.example .env
```

Open the `.env` file and update the following values:

- OPENAI_API_KEY
- ASSEMBLYAI_API_KEY
- POSTGRES_HOST
- POSTGRES_PORT
- POSTGRES_DB
- POSTGRES_USER
- POSTGRES_PASSWORD
- REDIS_HOST
- REDIS_PORT

---

## Running the Executable

### macOS

```
./EducationAI
```

### Windows

```
EducationAI.exe
```

---

## API Documentation

Once the server starts successfully, open:

```
http://127.0.0.1:8000/docs
```

Health Check:

```
http://127.0.0.1:8000/
```

---

## Common Issues

### PostgreSQL Connection Failed

- Verify PostgreSQL is running.
- Verify database credentials in `.env`.
- Verify the database exists.

---

### Redis Connection Failed

- Verify Redis server is running.
- Verify Redis host and port.

---

### Invalid OpenAI API Key

- Verify the OpenAI API key.
- Restart the application after updating `.env`.

---

### Invalid AssemblyAI API Key

- Verify the AssemblyAI API key.
- Restart the application after updating `.env`.

---

### Port 8000 Already in Use

Stop the existing process using port 8000 or change the application port in the configuration.

---

## Security Notes

- Never share your `.env` file.
- Never commit API keys to GitHub.
- Use `.env.example` when sharing the project.
- Keep PostgreSQL credentials private.

---

## Distribution Package

The application should be distributed with:

```
EducationAI (macOS executable)

or

EducationAI.exe (Windows executable)

.env.example

README.md
```

---

## License

This project is developed for educational and academic purposes.

---

## Author

Saloni Ganvir

M.Sc. Artificial Intelligence & Data Analytics

Amity University Noida