import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { NewInterview } from './pages/NewInterview'
import { InterviewSession } from './pages/InterviewSession'

const router = createBrowserRouter([
  { path: '/', element: <Layout />, children: [
    { index: true, element: <Dashboard /> },
    { path: 'new', element: <NewInterview /> },
    { path: 'sessions/:id', element: <InterviewSession /> },
  ]},
])

export default function App() { return <RouterProvider router={router} /> }
