import type { Evaluation, Question, SessionDetail, SessionSummary } from './types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, options)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      message = body.detail || message
    } catch {
      // keep fallback
    }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export const api = {
  listSessions: () => request<SessionSummary[]>('/api/sessions'),
  getSession: (id: string) => request<SessionDetail>(`/api/sessions/${id}`),
  createSession: (form: FormData) => request<SessionDetail>('/api/sessions', { method: 'POST', body: form }),
  generateQuestions: (id: string) => request<Question[]>(`/api/sessions/${id}/generate`, { method: 'POST' }),
  submitAnswer: (questionId: string, answer: string) =>
    request<Evaluation>(`/api/sessions/questions/${questionId}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer }),
    }),
}
