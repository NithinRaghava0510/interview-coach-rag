export type Evidence = {
  source: string
  chunk_index: number
  excerpt: string
}

export type Evaluation = {
  id: string
  answer: string
  overall_score: number
  relevance_score: number
  clarity_score: number
  structure_score: number
  technical_score: number
  strengths: string[]
  improvements: string[]
  stronger_answer: string
  created_at: string
}

export type Question = {
  id: string
  position: number
  category: string
  question: string
  why_asked: string
  source_evidence: Evidence[]
  evaluation?: Evaluation | null
}

export type SessionSummary = {
  id: string
  role: string
  difficulty: string
  question_count: number
  resume_filename: string
  status: string
  created_at: string
  answered_count: number
  average_score?: number | null
}

export type SessionDetail = SessionSummary & {
  job_description: string
  questions: Question[]
}
