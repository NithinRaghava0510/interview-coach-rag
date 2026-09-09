import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export function NewInterview() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [file, setFile] = useState<File | null>(null)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    if (!file) return setError('Choose a resume file first.')
    const formElement = event.currentTarget
    const form = new FormData(formElement)
    form.set('resume', file)
    setLoading(true)
    try {
      const session = await api.createSession(form)
      await api.generateQuestions(session.id)
      navigate(`/sessions/${session.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setLoading(false)
    }
  }

  return (
    <section className="form-layout">
      <div className="form-intro">
        <span className="eyebrow">New interview</span>
        <h1>Turn your resume and target role into a focused interview loop.</h1>
        <p>The backend extracts both documents, chunks them, embeds the chunks, retrieves relevant evidence, and uses that context to generate questions.</p>
        <div className="architecture-mini">
          <span>Resume/JD</span><b>→</b><span>Chunks</span><b>→</b><span>pgvector</span><b>→</b><span>RAG</span><b>→</b><span>Interview</span>
        </div>
      </div>

      <form className="panel form-panel" onSubmit={submit}>
        <label>Target role<input name="role" required placeholder="e.g. Senior Full Stack Engineer" /></label>
        <div className="two-col">
          <label>Difficulty<select name="difficulty" defaultValue="medium"><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></label>
          <label>Questions<select name="question_count" defaultValue="6"><option>3</option><option>4</option><option>5</option><option>6</option><option>8</option><option>10</option><option>12</option></select></label>
        </div>
        <label>Resume (.pdf, .docx, .txt)
          <div className="file-drop"><input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setFile(e.target.files?.[0] || null)} /><span>{file ? file.name : 'Choose your resume'}</span></div>
        </label>
        <label>Job description<textarea name="job_description" required rows={12} placeholder="Paste the full job description here..." /></label>
        {error && <div className="alert error">{error}</div>}
        <button className="button full" disabled={loading}>{loading ? 'Indexing and generating…' : 'Build my interview'}</button>
        <p className="form-note">Tip: with DEMO_MODE=true you can run the whole workflow without an API key.</p>
      </form>
    </section>
  )
}
