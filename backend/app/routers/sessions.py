from statistics import mean
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import AnswerEvaluation, DocumentChunk, InterviewQuestion, InterviewSession
from app.schemas import AnswerIn, EvaluationOut, QuestionOut, SessionDetail, SessionSummary
from app.services.document_parser import chunk_text, extract_text
from app.services.embeddings import embedding_service
from app.services.llm import llm_service
from app.services.rag import evidence_from_chunks, format_context, retrieve_context

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _summary(session: InterviewSession) -> SessionSummary:
    evaluations = [q.evaluation for q in session.questions if q.evaluation]
    return SessionSummary(
        id=session.id,
        role=session.role,
        difficulty=session.difficulty,
        question_count=session.question_count,
        resume_filename=session.resume_filename,
        status=session.status,
        created_at=session.created_at,
        answered_count=len(evaluations),
        average_score=round(mean(e.overall_score for e in evaluations), 1) if evaluations else None,
    )


def _detail(session: InterviewSession) -> SessionDetail:
    base = _summary(session)
    return SessionDetail(
        **base.model_dump(),
        job_description=session.job_description,
        questions=[QuestionOut.model_validate(q) for q in session.questions],
    )


@router.get("", response_model=list[SessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    statement = select(InterviewSession).options(selectinload(InterviewSession.questions).selectinload(InterviewQuestion.evaluation)).order_by(InterviewSession.created_at.desc())
    sessions = db.scalars(statement).all()
    return [_summary(session) for session in sessions]


@router.post("", response_model=SessionDetail, status_code=201)
async def create_session(
    role: str = Form(...),
    difficulty: str = Form("medium"),
    question_count: int = Form(6),
    job_description: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if difficulty not in {"easy", "medium", "hard"}:
        raise HTTPException(400, "difficulty must be easy, medium, or hard")
    if question_count < 3 or question_count > 12:
        raise HTTPException(400, "question_count must be between 3 and 12")
    if len(job_description.strip()) < 80:
        raise HTTPException(400, "Please paste a more complete job description.")

    try:
        resume_bytes = await resume.read()
        resume_text = extract_text(resume.filename or "resume.txt", resume_bytes)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    session = InterviewSession(
        role=role.strip(),
        difficulty=difficulty,
        question_count=question_count,
        resume_filename=resume.filename or "resume",
        job_description=job_description.strip(),
        status="indexing",
    )
    db.add(session)
    db.flush()

    records: list[tuple[str, int, str]] = []
    for source_type, text_value in (("resume", resume_text), ("job_description", job_description)):
        for index, chunk in enumerate(chunk_text(text_value)):
            records.append((source_type, index, chunk))

    try:
        vectors = embedding_service.embed([record[2] for record in records])
        for (source_type, index, content), vector in zip(records, vectors, strict=True):
            db.add(DocumentChunk(session_id=session.id, source_type=source_type, chunk_index=index, content=content, embedding=vector))
        session.status = "ready"
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, f"Indexing failed: {exc}") from exc

    statement = select(InterviewSession).where(InterviewSession.id == session.id).options(selectinload(InterviewSession.questions).selectinload(InterviewQuestion.evaluation))
    return _detail(db.scalar(statement))


@router.post("/{session_id}/generate", response_model=list[QuestionOut])
def generate_questions(session_id: UUID, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(404, "Interview session not found")

    db.execute(delete(InterviewQuestion).where(InterviewQuestion.session_id == session_id))
    query = f"Key skills, responsibilities, projects and requirements for {session.role}. Technical depth and interview evidence."
    chunks = retrieve_context(db, session_id, query, limit=10)
    context = format_context(chunks)
    try:
        generated = llm_service.generate_questions(session.role, session.difficulty, session.question_count, context)
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, f"Question generation failed: {exc}") from exc

    questions = []
    for index, item in enumerate(generated, start=1):
        question_text = str(item.get("question", "Explain a relevant project."))
        question_chunks = retrieve_context(db, session_id, question_text, limit=3)
        question = InterviewQuestion(
            session_id=session_id,
            position=index,
            category=str(item.get("category", "Technical"))[:80],
            question=question_text,
            why_asked=str(item.get("why_asked", "Assesses role-relevant depth.")),
            source_evidence=evidence_from_chunks(question_chunks),
        )
        db.add(question)
        questions.append(question)
    db.commit()
    for question in questions:
        db.refresh(question)
    return [QuestionOut.model_validate(q) for q in questions]


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: UUID, db: Session = Depends(get_db)):
    statement = select(InterviewSession).where(InterviewSession.id == session_id).options(selectinload(InterviewSession.questions).selectinload(InterviewQuestion.evaluation))
    session = db.scalar(statement)
    if not session:
        raise HTTPException(404, "Interview session not found")
    return _detail(session)


@router.post("/questions/{question_id}/answer", response_model=EvaluationOut)
def submit_answer(question_id: UUID, payload: AnswerIn, db: Session = Depends(get_db)):
    statement = select(InterviewQuestion).where(InterviewQuestion.id == question_id).options(selectinload(InterviewQuestion.session), selectinload(InterviewQuestion.evaluation))
    question = db.scalar(statement)
    if not question:
        raise HTTPException(404, "Question not found")

    query = f"{question.question} Ideal evidence, projects, tools, responsibilities and technical details relevant to answering this interview question."
    chunks = retrieve_context(db, question.session_id, query, limit=6)
    context = format_context(chunks)
    try:
        result = llm_service.evaluate_answer(question.session.role, question.question, payload.answer, context)
    except Exception as exc:
        raise HTTPException(500, f"Evaluation failed: {exc}") from exc

    evaluation = question.evaluation or AnswerEvaluation(question_id=question.id, answer=payload.answer, overall_score=0, relevance_score=0, clarity_score=0, structure_score=0, technical_score=0, stronger_answer="")
    evaluation.answer = payload.answer
    evaluation.overall_score = float(result.get("overall_score", 0))
    evaluation.relevance_score = float(result.get("relevance_score", 0))
    evaluation.clarity_score = float(result.get("clarity_score", 0))
    evaluation.structure_score = float(result.get("structure_score", 0))
    evaluation.technical_score = float(result.get("technical_score", 0))
    evaluation.strengths = list(result.get("strengths", []))
    evaluation.improvements = list(result.get("improvements", []))
    evaluation.stronger_answer = str(result.get("stronger_answer", ""))
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return EvaluationOut.model_validate(evaluation)
