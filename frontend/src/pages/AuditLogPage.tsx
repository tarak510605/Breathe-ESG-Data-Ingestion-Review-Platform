import { useState, useEffect } from 'react'
import { auditAPI, AuditLog } from '../api/audit'

const ACTION_COLORS = {
  created: 'bg-blue-100 text-blue-800',
  edited: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  locked: 'bg-gray-100 text-gray-800',
  comment_added: 'bg-purple-100 text-purple-800',
}

export default function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    loadLogs()
  }, [currentPage])

  const loadLogs = async () => {
    setIsLoading(true)
    try {
      const response = await auditAPI.listLogs(undefined, currentPage)
      setLogs(response.data.results)
      setTotalCount(response.data.count)
    } catch (error) {
      console.error('Failed to load audit logs:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getActionColor = (action: string) => {
    return ACTION_COLORS[action as keyof typeof ACTION_COLORS] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  if (isLoading && logs.length === 0) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
      
      {logs.length === 0 ? (
        <div className="card">
          <p className="text-center text-gray-600 py-8">
            No audit logs found
          </p>
        </div>
      ) : (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Timestamp</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Action</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">User</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Record Type</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Reason</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${getActionColor(log.action)}`}>
                        {log.action.charAt(0).toUpperCase() + log.action.slice(1)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-900">
                      {log.user_email}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {log.record_type}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {log.change_reason || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalCount > logs.length && (
            <div className="mt-4 flex justify-center gap-2">
              <button
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-4 py-2">
                Page {currentPage}
              </span>
              <button
                onClick={() => setCurrentPage(p => p + 1)}
                disabled={logs.length < 20}
                className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
