import { useState, useEffect } from 'react'
import { ingestionAPI, IngestionJob } from '../api/ingestion'
import { emissionsAPI } from '../api/emissions'

export default function DashboardPage() {
  const [jobs, setJobs] = useState<IngestionJob[]>([])
  const [metrics, setMetrics] = useState({
    total_records: 0,
    approved: 0,
    pending: 0,
    failed: 0,
  })
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setIsLoading(true)
    try {
      const [jobsRes, recordsRes] = await Promise.all([
        ingestionAPI.listJobs(),
        emissionsAPI.listRecords(),
      ])

      setJobs(jobsRes.data.results.slice(0, 5))
      
      // Calculate metrics
      const records = recordsRes.data.results
      setMetrics({
        total_records: recordsRes.data.count,
        approved: records.filter(r => r.review_decision === 'approved').length,
        pending: records.filter(r => r.review_decision === 'pending').length,
        failed: records.filter(r => r.status === 'rejected').length,
      })
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusBadgeClass = (status: string) => {
    const classes = 'badge'
    if (status === 'completed') return `${classes} badge-success`
    if (status === 'processing') return `${classes} badge-info`
    if (status === 'failed') return `${classes} badge-danger`
    return `${classes} badge-warning`
  }

  if (isLoading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-gray-600">Total Records</p>
          <p className="text-3xl font-bold text-blue-600">{metrics.total_records}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600">Approved</p>
          <p className="text-3xl font-bold text-green-600">{metrics.approved}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600">Pending Review</p>
          <p className="text-3xl font-bold text-yellow-600">{metrics.pending}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-600">Failed</p>
          <p className="text-3xl font-bold text-red-600">{metrics.failed}</p>
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Recent Ingestion Jobs</h2>
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>File Name</th>
                <th>Status</th>
                <th>Records</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td className="font-medium">{job.file_name}</td>
                  <td>
                    <span className={getStatusBadgeClass(job.status)}>
                      {job.status}
                    </span>
                  </td>
                  <td>
                    {job.total_records}
                    <span className="text-xs text-gray-500 ml-2">
                      ({job.valid_records} valid)
                    </span>
                  </td>
                  <td className="text-sm text-gray-600">
                    {new Date(job.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
