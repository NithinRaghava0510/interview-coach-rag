import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'
import { ScoreBar } from '../components/ScoreBar'
import type { Evaluation, SessionDetail } from '../types'

export function InterviewSession() {
  const { id = '' } = useParams()
  const [session, setSession] = useState<SessionDetail | null>(null)
  const [active, setActive] = useState(0)
  const [answer, setAnswer] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    try { setSession(await api.getSession(id)) } catch (err) { setError(err instanceof Error ? err.message : 'Failed to load') }
  }

  useEffect(() => { load() }, [id])

  const question = session?.questions[active]
  useEffect(() => { setAnswer(question?.evaluation?.answer || '') }, [question?.id])

  const completed = useMemo(() => session?.questions.filter((q) => q.evaluation).length || 0, [session])

  async function submitAnswer() {
    if (!question || answer.trim().length < 10) return
    setSubmitting(true); setError('')
    try {
      const evaluation: Evaluation = await api.submitAnswer(question.id, answer.trim())
      setSession((current) => current ? ({ ...current, questions: current.questions.map((q) => q.id === question.id ? { ...q, evaluation } : q) }) : current)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Evaluation failed')
    } finally { setSubmitting(false) }
  }

  if (error && !session) return <div className="alert error">{error}</div>
  if (!session || !question) return <div className="loading">Loading interview…</div>
  const evaluation = question.evaluation

  return (
    <div className="interview-layout">
      <aside className="question-nav panel">
        <span className="eyebrow">{session.difficulty} interview</span>
        <h2>{session.role}</h2>
        <p>{completed}/{session.questions.length} answered</p>
        <div className="progress"><div style={{ width: `${(completed / session.questions.length) * 100}%` }} /></div>
        <div className="question-list">
          {session.questions.map((q, index) => (
            <button key={q.id} className={`${index === active ? 'active' : ''} ${q.evaluation ? 'done' : ''}`} onClick={() => setActive(index)}>
              <span>{String(index + 1).padStart(2, '0')}</span><div><strong>{q.category}</strong><small>{q.evaluation ? `${Math.round(q.evaluation.overall_score)}/100` : 'Not answered'}</small></div>
            </button>
          ))}
        </div>
      </aside>

      <section className="interview-main">
        <div className="question-card panel">
          <div className="question-meta"><span className="pill">{question.category}</span><span>Question {active + 1} of {session.questions.length}</span></div>
          <h1>{question.question}</h1>
          <details className="why-box"><summary>Why this question was selected</summary><p>{question.why_asked}</p></details>
          <label className="answer-label">Your answer<textarea rows={10} value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Answer as if you were speaking to the interviewer. Use concrete decisions, tradeoffs, and results." /></label>
          {error && <div className="alert error">{error}</div>}
          <div className="answer-actions">
            <button className="button" disabled={submitting || answer.trim().length < 10} onClick={submitAnswer}>{submitting ? 'Evaluating…' : evaluation ? 'Re-evaluate answer' : 'Evaluate answer'}</button>
            {active < session.questions.length - 1 && <button className="button secondary" onClick={() => setActive(active + 1)}>Next question</button>}
          </div>
        </div>

        {evaluation && (
          <div className="evaluation-grid">
            <section className="panel score-panel">
              <div className="overall-score"><div>{Math.round(evaluation.overall_score)}</div><span>overall score</span></div>
              <ScoreBar label="Relevance" value={evaluation.relevance_score} />
              <ScoreBar label="Clarity" value={evaluation.clarity_score} />
              <ScoreBar label="Structure" value={evaluation.structure_score} />
              <ScoreBar label="Technical depth" value={evaluation.technical_score} />
            </section>
            <section className="panel feedback-panel">
              <div><h3>What worked</h3><ul>{evaluation.strengths.map((item) => <li key={item}>{item}</li>)}</ul></div>
              <div><h3>Improve next</h3><ul>{evaluation.improvements.map((item) => <li key={item}>{item}</li>)}</ul></div>
            </section>
            <section className="panel stronger-panel"><span className="eyebrow">Stronger version</span><h3>A tighter answer you can practice</h3><p>{evaluation.stronger_answer}</p></section>
          </div>
        )}

        <details className="panel evidence-panel">
          <summary>Retrieved evidence used for this question</summary>
          <div className="evidence-list">{question.source_evidence.map((e, idx) => <div key={`${e.source}-${idx}`}><span>{e.source.replace('_', ' ')} #{e.chunk_index}</span><p>{e.excerpt}</p></div>)}</div>
        </details>
      </section>
    </div>
  )
}
