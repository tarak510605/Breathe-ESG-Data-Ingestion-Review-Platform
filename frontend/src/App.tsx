import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import IngestionsPage from './pages/IngestionsPage'
import ReviewQueuePage from './pages/ReviewQueuePage'
import AuditLogPage from './pages/AuditLogPage'

function App() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        
        {isAuthenticated ? (
          <Route element={<Layout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/ingestions" element={<IngestionsPage />} />
            <Route path="/review-queue" element={<ReviewQueuePage />} />
            <Route path="/audit-logs" element={<AuditLogPage />} />
          </Route>
        ) : (
          <Route path="*" element={<Navigate to="/login" replace />} />
        )}
      </Routes>
    </Router>
  )
}

export default App
