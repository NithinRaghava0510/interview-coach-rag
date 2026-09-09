import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import settings
from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role: Mapped[str] = mapped_column(String(180))
    difficulty: Mapped[str] = mapped_column(String(40), default="medium")
    question_count: Mapped[int] = mapped_column(Integer, default=6)
    resume_filename: Mapped[str] = mapped_column(String(255))
    job_description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="ready")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    questions: Mapped[list["InterviewQuestion"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.position")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True)
    source_type: Mapped[str] = mapped_column(String(40))  # resume | job_description
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dimensions))

    session: Mapped[InterviewSession] = relationship(back_populates="chunks")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(80))
    question: Mapped[str] = mapped_column(Text)
    why_asked: Mapped[str] = mapped_column(Text)
    source_evidence: Mapped[list] = mapped_column(JSONB, default=list)

    session: Mapped[InterviewSession] = relationship(back_populates="questions")
    evaluation: Mapped["AnswerEvaluation | None"] = relationship(back_populates="question", cascade="all, delete-orphan", uselist=False)


class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_questions.id", ondelete="CASCADE"), unique=True, index=True)
    answer: Mapped[str] = mapped_column(Text)
    overall_score: Mapped[float] = mapped_column(Float)
    relevance_score: Mapped[float] = mapped_column(Float)
    clarity_score: Mapped[float] = mapped_column(Float)
    structure_score: Mapped[float] = mapped_column(Float)
    technical_score: Mapped[float] = mapped_column(Float)
    strengths: Mapped[list] = mapped_column(JSONB, default=list)
    improvements: Mapped[list] = mapped_column(JSONB, default=list)
    stronger_answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    question: Mapped[InterviewQuestion] = relationship(back_populates="evaluation")
