import { Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export default function Layout() {
  const navigate = useNavigate()
  const logout = useAuthStore((state) => state.logout)
  const user = useAuthStore((state) => state.user)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-blue-600">Breathe ESG</h1>
          <p className="text-sm text-gray-600 mt-2">Data Ingestion Platform</p>
        </div>

        <nav className="mt-8">
          <ul className="space-y-2 px-4">
            <li>
              <a
                href="/"
                className="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600"
              >
                Dashboard
              </a>
            </li>
            <li>
              <a
                href="/ingestions"
                className="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600"
              >
                Ingestions
              </a>
            </li>
            <li>
              <a
                href="/review-queue"
                className="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600"
              >
                Review Queue
              </a>
            </li>
            <li>
              <a
                href="/audit-logs"
                className="block px-4 py-2 rounded-lg hover:bg-blue-50 text-gray-700 hover:text-blue-600"
              >
                Audit Logs
              </a>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="px-6 py-4 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900"></h2>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                {user?.email}
              </span>
              <button
                onClick={handleLogout}
                className="btn btn-secondary text-sm"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
