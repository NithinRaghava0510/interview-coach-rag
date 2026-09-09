export function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-row">
      <div className="score-label"><span>{label}</span><strong>{Math.round(value)}</strong></div>
      <div className="score-track"><div className="score-fill" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} /></div>
    </div>
  )
}
