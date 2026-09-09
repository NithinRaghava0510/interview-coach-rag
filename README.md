Interview Coach RAG

Interview Coach RAG is a full-stack interview practice app that generates questions from a candidate's resume and a target job description, then evaluates answers using the same source material as context.

The main goal of the project was to build a RAG workflow around a real use case instead of a generic "chat with a PDF" example. The application handles document ingestion, chunking, embeddings, vector retrieval, question generation, answer evaluation, and interview history from one UI.

Features

Upload a resume as PDF, DOCX, or TXT

Add a job description for the role being targeted

Generate interview questions based on both documents

Store resume and job-description chunks in PostgreSQL with pgvector

Retrieve relevant context for each question using vector similarity

Submit answers and get structured feedback

Score answers on relevance, clarity, structure, and technical depth

Keep previous interview sessions and evaluations in PostgreSQL

Run the full application in demo mode without an OpenAI API key

Start the local database with Docker Compose

Tech stack

Backend

Python

FastAPI

SQLAlchemy

Pydantic

PostgreSQL

pgvector

OpenAI API

Frontend

React

TypeScript

Vite

React Router

Local infrastructure

Docker / Docker Compose

PostgreSQL 17 + pgvector

GitHub Actions

How it works

The application uses the resume and job description as the knowledge base for an interview session.

Resume + Job Description
          |
          v
    Text extraction
          |
          v
       Chunking
          |
          v
      Embeddings
          |
          v
 PostgreSQL + pgvector
          |
          v
   Similarity search
          |
          v
 Retrieved resume/JD context
          |
          +--------------------+
          |                    |
          v                    v
 Question generation     Answer evaluation

When a new interview is created, the backend extracts text from the uploaded resume, splits the resume and job description into chunks, creates an embedding for each chunk, and stores everything with the interview session.

Question generation starts by retrieving the chunks that are most relevant to the target role. Those chunks are used as context so the questions are tied to the candidate's actual experience and the requirements in the job description.

The retrieval step runs again when an answer is submitted. The evaluator receives the question, the candidate's answer, and the most relevant resume/JD context, then returns scores, strengths, improvement areas, and a stronger example answer.

Project structure

interview-coach-rag/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   └── sessions.py
│   │   ├── services/
│   │   │   ├── document_parser.py
│   │   │   ├── embeddings.py
│   │   │   ├── llm.py
│   │   │   └── rag.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles.css
│   ├── .env.example
│   └── package.json
├── sample-data/
├── .github/workflows/ci.yml
├── docker-compose.yml
└── README.md

Local setup

I use three terminals while developing locally: one for PostgreSQL, one for FastAPI, and one for Vite.

Prerequisites

Install the following before starting:

Python 3.11 or 3.12

Node.js 22+

Docker Desktop

Git

VS Code is optional, but the commands below assume the project is opened from its root folder in a VS Code terminal.

1. Start PostgreSQL

From the project root:

docker compose up -d postgres

Check the container:

docker compose ps

The local database configuration is:

Database: interview_coach
User:     interview
Password: interview
Host:     localhost
Port:     5432

The backend enables the vector extension and creates the application tables on startup.

2. Set up the backend

Open another terminal:

cd backend
Copy-Item .env.example .env
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt

Start FastAPI:

.venv\Scripts\python -m uvicorn app.main:app --reload

The API will be available at:

http://localhost:8000

Swagger UI:

http://localhost:8000/docs

Health check:

http://localhost:8000/health

For macOS/Linux, replace .venv\Scripts\python with .venv/bin/python and use cp .env.example .env instead of Copy-Item.

3. Set up the frontend

Open a third terminal:

cd frontend
Copy-Item .env.example .env
npm install
npm run dev

Vite will start the frontend at:

http://localhost:5173

Environment variables

The backend example environment file contains the local defaults:

APP_NAME=Interview Coach RAG
API_PREFIX=/api
DATABASE_URL=postgresql+psycopg://interview:interview@localhost:5432/interview_coach
CORS_ORIGINS=http://localhost:5173
OPENAI_API_KEY=
CHAT_MODEL=gpt-5.6-luna
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
DEMO_MODE=true

The frontend only needs the API URL:

VITE_API_URL=http://localhost:8000

.env files are ignored by Git. API keys should never be committed to the repository.

Demo mode

The project defaults to DEMO_MODE=true so the application can be run without an API key.

This mode was useful while building the ingestion, retrieval, database, and frontend flows because those parts could be tested without making an API request every time.

Demo mode still uses the same main application flow:

documents are parsed and chunked;

chunks are persisted in PostgreSQL;

deterministic local vectors are generated;

vector similarity search runs through pgvector;

fallback question generation creates interview questions;

fallback evaluation returns deterministic feedback.

There are two small files in sample-data/ that can be used to test the application immediately:

sample-data/sample_resume.txt
sample-data/sample_job_description.txt

Using the OpenAI API

Once the local flow is working, update backend/.env:

OPENAI_API_KEY=your_api_key_here
DEMO_MODE=false

Then restart FastAPI.

With demo mode disabled, the embedding service uses the configured OpenAI embedding model and the LLM service handles question generation and answer evaluation.

The current embedding configuration uses 1536 dimensions. If the embedding model or dimension is changed, the pgvector column and existing local data need to stay compatible.

For a clean development reset:

docker compose down -v
docker compose up -d postgres

Data model

The database is intentionally small for the first version of the application.

InterviewSession

Stores the role, difficulty, job description, resume file name, and creation time for an interview.

DocumentChunk

Stores individual resume/job-description chunks and their vector embeddings.

InterviewQuestion

Stores generated questions, category, display position, explanation for why the question was asked, and source evidence.

AnswerEvaluation

Stores the submitted answer and all evaluation results.

The relationships are roughly:

InterviewSession
    |
    +--- DocumentChunk
    |
    +--- InterviewQuestion
              |
              +--- AnswerEvaluation

API endpoints

The current API is deliberately small:

GET    /health
GET    /api/sessions
POST   /api/sessions
GET    /api/sessions/{session_id}
POST   /api/sessions/{session_id}/generate
POST   /api/sessions/questions/{question_id}/answer

For development, Swagger is the easiest way to inspect request/response schemas and test individual endpoints:

http://localhost:8000/docs

Running tests

Backend tests:

cd backend
.venv\Scripts\python -m pytest

Frontend production build:

cd frontend
npm run build

The repository also contains a GitHub Actions workflow for basic CI checks.

A few implementation choices

PostgreSQL + pgvector instead of a separate vector database

For this project, keeping relational data and embeddings in the same database made the architecture simpler. Interview sessions, questions, evaluations, source chunks, and vectors all belong to the same domain, so PostgreSQL is enough for the current scale.

It also makes local development easier because only one data service has to be started.

Retrieval happens twice

Retrieval is not only used when generating questions. It runs again when an answer is evaluated.

That second retrieval is important because the context that is useful for generating a question is not always the best context for evaluating the resulting answer.

Demo mode uses the same application path

I did not want a demo switch that simply returned hard-coded frontend data. Demo mode replaces the external model calls, but documents still go through parsing, chunking, persistence, and vector retrieval. This made it much more useful for debugging the actual application.

No authentication in the first version

The first version is focused on the interview/RAG workflow. There is no user-account system yet, so the current app should be treated as a local/single-user project rather than a production multi-tenant service.

Known limitations

A few things are intentionally simple right now:

chunking is lightweight and not document-layout aware;

retrieval is vector-only rather than hybrid search;

there is no reranking stage;

sessions are not tied to authenticated users;

document ingestion happens in the request path instead of a background worker;

the current UI is text based and does not include voice interviews;

database schema changes are created directly rather than managed through migrations.

These are the main areas I would address before treating the project as a production application.

Next steps

The next improvements I want to make are:

Add JWT authentication and per-user interview history.

Add follow-up questions based on the previous answer.

Add hybrid keyword + vector retrieval and reranking.

Move document ingestion to a background worker.

Add Redis for caching/session support.

Add voice input and speech-to-text for mock interviews.

Add Alembic migrations.

Add retrieval/evaluation metrics so RAG quality can be measured instead of judged only from the UI.

Store uploaded documents in S3 when deploying to AWS.

Deploy the backend, frontend, PostgreSQL, and supporting services to AWS.

