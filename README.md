# Interview Coach RAG

A full-stack, portfolio-ready interview coaching application built with **FastAPI, React, TypeScript, PostgreSQL, pgvector, and OpenAI**.

The application takes a candidate resume and a target job description, indexes both documents into PostgreSQL/pgvector, retrieves relevant evidence, generates personalized interview questions, evaluates candidate answers, and stores interview history and scores.

## What this project demonstrates

- FastAPI REST API design
- React + TypeScript frontend development
- PostgreSQL relational modeling
- pgvector semantic similarity search
- RAG ingestion, chunking, embeddings, retrieval, and grounded generation
- Resume parsing for PDF, DOCX, and TXT
- OpenAI Responses API and embeddings
- Demo mode that works without an API key
- Docker-based local database setup
- GitHub Actions CI
- Production-minded error handling, CORS, typed schemas, and environment configuration

---

## Architecture

```text
                   ┌───────────────────────────┐
                   │      React + TypeScript   │
                   │          Vite UI          │
                   └─────────────┬─────────────┘
                                 │ HTTP / JSON
                                 ▼
                   ┌───────────────────────────┐
                   │          FastAPI          │
                   │  Sessions / Questions /  │
                   │       Evaluations         │
                   └─────────────┬─────────────┘
                                 │
                ┌────────────────┼────────────────┐
                │                │                │
                ▼                ▼                ▼
        Resume/JD parser   Embedding service   LLM service
                │                │                │
                └──────────────┬─┴────────────────┘
                               ▼
                   ┌───────────────────────────┐
                   │ PostgreSQL + pgvector     │
                   │ sessions / chunks /      │
                   │ questions / evaluations  │
                   └───────────────────────────┘
```

### RAG flow

```text
Resume + Job Description
          ↓
   Text extraction
          ↓
      Chunking
          ↓
      Embeddings
          ↓
 PostgreSQL + pgvector
          ↓
 Semantic retrieval
          ↓
 Retrieved evidence
          ↓
 Question generation
          ↓
 Candidate answer
          ↓
 Evidence retrieval again
          ↓
 Grounded evaluation
```

---

# 1. Install the prerequisites

For the smoothest setup, install:

- **Git**
- **VS Code**
- **Python 3.11 or 3.12**
- **Node.js 22**
- **Docker Desktop**

You can verify everything from PowerShell:

```powershell
git --version
py --version
node --version
npm --version
docker --version
```

Recommended versions:

```text
Python: 3.11 or 3.12
Node:   22.x
Docker: current Docker Desktop
```

---

# 2. Open the project in VS Code

If you downloaded the ZIP generated with this project:

1. Extract `interview-coach-rag.zip`.
2. Open VS Code.
3. Select **File → Open Folder**.
4. Choose the extracted `interview-coach-rag` folder.
5. Open **Terminal → New Terminal**.

You do **not** need to manually copy every source file into VS Code. The ZIP already contains the project structure.

The root should look like this:

```text
interview-coach-rag/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── services/
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
```

---

# 3. Start PostgreSQL + pgvector

From the **project root**:

```powershell
docker compose up -d postgres
```

Check that it is running:

```powershell
docker compose ps
```

You should see a PostgreSQL container running on port `5432`.

The database credentials used locally are:

```text
Database: interview_coach
Username: interview
Password: interview
Host:     localhost
Port:     5432
```

The FastAPI application automatically runs:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

and creates its tables on startup.

To stop the database later:

```powershell
docker compose down
```

To completely delete the local database and start over:

```powershell
docker compose down -v
```

---

# 4. Configure the backend

Open a new VS Code terminal.

```powershell
cd backend
Copy-Item .env.example .env
```

The initial `.env` uses **demo mode**:

```env
DEMO_MODE=true
OPENAI_API_KEY=
```

That is intentional. It lets you prove that the entire app works before paying for any API usage.

---

# 5. Create the Python virtual environment

Still inside `backend`:

```powershell
py -3.12 -m venv .venv
```

Install the dependencies without needing to activate the environment:

```powershell
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

If your machine only has one Python installation, this also works:

```powershell
py -m venv .venv
```

### macOS/Linux equivalent

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

---

# 6. Start FastAPI

On Windows:

```powershell
.venv\Scripts\python -m uvicorn app.main:app --reload
```

On macOS/Linux:

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

The backend should start at:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

FastAPI Swagger UI:

```text
http://localhost:8000/docs
```

Keep this terminal running.

---

# 7. Configure and start React

Open a **second VS Code terminal**.

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

The UI should start at:

```text
http://localhost:5173
```

Open that address in your browser.

---

# 8. Test the project without an OpenAI API key

The repository includes:

```text
sample-data/sample_resume.txt
sample-data/sample_job_description.txt
```

In the React UI:

1. Click **New interview**.
2. Set the target role to:

```text
Full Stack Software Engineer
```

3. Choose `sample_resume.txt`.
4. Paste the contents of `sample_job_description.txt`.
5. Select 6 questions.
6. Click **Build my interview**.
7. Answer one generated question.
8. Click **Evaluate answer**.

In demo mode:

- embeddings are deterministic local hashing vectors;
- semantic retrieval still runs through pgvector;
- question generation uses a local rule-based fallback;
- evaluation uses a deterministic scoring fallback.

This means you can test the database, vector retrieval, API, UI, persistence, and scoring workflow without spending money.

---

# 9. Turn on real RAG with OpenAI

After the demo version works, edit:

```text
backend/.env
```

Change:

```env
OPENAI_API_KEY=your_api_key_here
DEMO_MODE=false
```

The project currently defaults to:

```env
CHAT_MODEL=gpt-5.6-luna
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

Restart the FastAPI terminal after editing `.env`.

```powershell
Ctrl+C
.venv\Scripts\python -m uvicorn app.main:app --reload
```

### Important

Your ChatGPT subscription and OpenAI API billing are separate. An API key requires API-platform access/billing. Never commit your API key to GitHub.

The included `.gitignore` already ignores:

```text
backend/.env
frontend/.env
```

---

# 10. What happens when you create an interview

The frontend sends this data to FastAPI:

```text
role
difficulty
question_count
resume file
job description
```

FastAPI then:

1. Extracts resume text.
2. Chunks the resume.
3. Chunks the job description.
4. Creates embeddings.
5. Stores chunks and embeddings in PostgreSQL/pgvector.
6. Creates an interview session.
7. Retrieves the chunks most relevant to the role.
8. Generates personalized questions.
9. Saves the generated questions.

When you answer a question:

1. FastAPI embeds the interview question.
2. pgvector retrieves relevant resume/JD chunks again.
3. The answer, question, and retrieved evidence are sent to the evaluator.
4. The evaluator returns:
   - overall score
   - relevance score
   - clarity score
   - structure score
   - technical-depth score
   - strengths
   - areas to improve
   - a stronger sample answer
5. The result is stored in PostgreSQL.

---

# 11. Database model

```text
InterviewSession
├── id
├── role
├── difficulty
├── job_description
├── resume_filename
└── created_at

DocumentChunk
├── session_id
├── source_type
├── chunk_index
├── content
└── embedding VECTOR(1536)

InterviewQuestion
├── session_id
├── position
├── category
├── question
├── why_asked
└── source_evidence JSONB

AnswerEvaluation
├── question_id
├── answer
├── overall_score
├── relevance_score
├── clarity_score
├── structure_score
├── technical_score
├── strengths JSONB
├── improvements JSONB
└── stronger_answer
```

---

# 12. Main API routes

```text
GET    /health
GET    /api/sessions
POST   /api/sessions
GET    /api/sessions/{session_id}
POST   /api/sessions/{session_id}/generate
POST   /api/sessions/questions/{question_id}/answer
```

You can test them manually in Swagger at:

```text
http://localhost:8000/docs
```

---

# 13. Recommended VS Code extensions

Useful, but optional:

- Python
- Pylance
- FastAPI
- ESLint
- Prettier
- Docker
- GitLens
- PostgreSQL database client extension

---

# 14. Run the backend test

From `backend`:

```powershell
.venv\Scripts\python -m pytest
```

macOS/Linux:

```bash
.venv/bin/python -m pytest
```

---

# 15. Build the frontend for production

From `frontend`:

```powershell
npm run build
```

The production bundle will be generated in:

```text
frontend/dist
```

---

# 16. Put the project on GitHub

From the root `interview-coach-rag` folder:

```powershell
git init
git add .
git commit -m "Build RAG-powered full stack interview coach"
git branch -M main
```

Create a new empty repository on GitHub named:

```text
interview-coach-rag
```

Then connect your repository using the remote command GitHub gives you, followed by:

```powershell
git push -u origin main
```

### If you use GitHub CLI

```powershell
gh auth login
gh repo create interview-coach-rag --public --source=. --remote=origin --push
```

Before pushing, verify that secrets are not staged:

```powershell
git status
```

You should **not** see `backend/.env` in the files being committed.

---

# 17. Suggested GitHub repository description

```text
Full-stack RAG interview coach built with FastAPI, React, PostgreSQL, pgvector and OpenAI. Generates resume/JD-grounded interview questions and evaluates candidate answers with retrieval-backed feedback.
```

Suggested GitHub topics:

```text
rag
fastapi
react
typescript
postgresql
pgvector
openai
llm
full-stack
ai
interview-preparation
```

---

# 18. Suggested resume bullet after you finish and deploy it

Do not use this until you have actually completed/deployed the project:

```text
Built a full-stack RAG interview coaching platform using FastAPI, React/TypeScript, PostgreSQL and pgvector, implementing document ingestion, vector retrieval, personalized question generation, evidence-grounded answer evaluation, persistent interview history, and Docker-based local infrastructure.
```

---

# 19. Troubleshooting

## `docker` is not recognized

Install Docker Desktop, start it, then reopen the VS Code terminal.

## Port 5432 is already in use

You probably already have PostgreSQL running locally. Either stop it or change this in `docker-compose.yml`:

```yaml
ports:
  - "5433:5432"
```

Then update `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://interview:interview@localhost:5433/interview_coach
```

## Backend cannot connect to PostgreSQL

Check:

```powershell
docker compose ps
docker compose logs postgres
```

## React says `Failed to fetch`

Make sure FastAPI is running on port 8000 and that `frontend/.env` contains:

```env
VITE_API_URL=http://localhost:8000
```

Restart Vite after changing `.env`.

## `ModuleNotFoundError`

Make sure the backend dependencies were installed using the virtual environment Python:

```powershell
.venv\Scripts\python -m pip install -r requirements.txt
```

## PowerShell blocks virtual-environment activation

You do not need to activate it. Use the explicit commands in this README:

```powershell
.venv\Scripts\python -m uvicorn app.main:app --reload
```

## OpenAI request fails

Check:

```env
OPENAI_API_KEY=...
DEMO_MODE=false
```

Then restart FastAPI. Also verify that the API account has usable billing/credits and access to the configured model.

## You changed the embedding model and get a vector dimension error

This project uses `text-embedding-3-small` with:

```env
EMBEDDING_DIMENSIONS=1536
```

If you change the embedding dimensions, delete/recreate the local database or create a proper migration before continuing.

For a clean local reset:

```powershell
docker compose down -v
docker compose up -d postgres
```

---

# 20. Strong next features for version 2

Once this MVP is working, add these one at a time instead of trying to do everything immediately:

1. JWT authentication and user accounts
2. GitHub/Google OAuth
3. Voice interview mode with speech-to-text
4. Streaming evaluation responses
5. Hybrid BM25 + vector retrieval
6. Reranking
7. RAG evaluation dashboard
8. Admin analytics
9. Resume/JD skill-gap extraction
10. Timed interview sessions
11. Follow-up questions based on previous answers
12. AWS deployment
13. Redis caching
14. Celery or another worker for asynchronous document ingestion
15. S3 document storage
16. HNSW pgvector index for larger datasets
17. Automated prompt/evaluation tests

A good progression is:

```text
v1: working local application
v2: authentication + richer RAG
v3: AWS deployment
v4: observability + async processing + evaluation metrics
```

---

# 21. Development commands cheat sheet

### Terminal 1 — database

```powershell
docker compose up -d postgres
```

### Terminal 2 — backend

```powershell
cd backend
.venv\Scripts\python -m uvicorn app.main:app --reload
```

### Terminal 3 — frontend

```powershell
cd frontend
npm run dev
```

### Browser

```text
UI:      http://localhost:5173
API:     http://localhost:8000
Swagger: http://localhost:8000/docs
```

---

## License

MIT
