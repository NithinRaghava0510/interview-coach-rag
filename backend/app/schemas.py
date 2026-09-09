from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationOut(BaseModel):
    id: UUID
    answer: str
    overall_score: float
    relevance_score: float
    clarity_score: float
    structure_score: float
    technical_score: float
    strengths: list[str]
    improvements: list[str]
    stronger_answer: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: UUID
    position: int
    category: str
    question: str
    why_asked: str
    source_evidence: list[dict]
    evaluation: EvaluationOut | None = None

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    id: UUID
    role: str
    difficulty: str
    question_count: int
    resume_filename: str
    status: str
    created_at: datetime
    answered_count: int = 0
    average_score: float | None = None


class SessionDetail(SessionSummary):
    job_description: str
    questions: list[QuestionOut] = []


class AnswerIn(BaseModel):
    answer: str = Field(min_length=10, max_length=12000)
