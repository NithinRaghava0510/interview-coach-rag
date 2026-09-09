import { Link, NavLink, Outlet } from 'react-router-dom'

export function Layout() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark">IC</span>
          <span>
            <strong>Interview Coach</strong>
            <small>RAG lab</small>
          </span>
        </Link>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/new" className="primary-nav">New interview</NavLink>
        </nav>
      </header>
      <main className="page-wrap"><Outlet /></main>
      <footer>FastAPI · React · PostgreSQL · pgvector · RAG</footer>
    </div>
  )
}
