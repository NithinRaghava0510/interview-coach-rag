import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { SessionSummary } from '../types'

export function Dashboard() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.listSessions().then(setSessions).catch((err: Error) => setError(err.message))
  }, [])

  return (
    <>
      <section className="hero">
        <div>
          <span className="eyebrow">Personalized technical prep</span>
          <h1>Practice the interview your resume is actually going to trigger.</h1>
          <p>Upload a resume, paste a job description, and generate evidence-grounded questions with answer scoring and stronger sample responses.</p>
          <div className="hero-actions"><Link to="/new" className="button">Start an interview</Link></div>
        </div>
        <div className="hero-card">
          <div><span>01</span><p>Resume + JD ingestion</p></div>
          <div><span>02</span><p>Vector retrieval</p></div>
          <div><span>03</span><p>Personalized questions</p></div>
          <div><span>04</span><p>Grounded evaluation</p></div>
        </div>
      </section>

      <section className="section-header">
        <div><span className="eyebrow">History</span><h2>Your interview sessions</h2></div>
        <Link to="/new" className="text-link">Create new →</Link>
      </section>

      {error && <div className="alert error">{error}. Is the FastAPI server running?</div>}
      {!error && sessions.length === 0 && (
        <div className="empty-state"><h3>No sessions yet</h3><p>Create your first interview to see RAG retrieval and scoring in action.</p></div>
      )}
      <div className="session-grid">
        {sessions.map((session) => (
          <Link className="session-card" to={`/sessions/${session.id}`} key={session.id}>
            <div className="card-top"><span className="pill">{session.difficulty}</span><span>{new Date(session.created_at).toLocaleDateString()}</span></div>
            <h3>{session.role}</h3>
            <p>{session.resume_filename}</p>
            <div className="card-stats">
              <div><strong>{session.answered_count}/{session.question_count}</strong><span>answered</span></div>
              <div><strong>{session.average_score == null ? '—' : Math.round(session.average_score)}</strong><span>avg score</span></div>
            </div>
          </Link>
        ))}
      </div>
    </>
  )
}
