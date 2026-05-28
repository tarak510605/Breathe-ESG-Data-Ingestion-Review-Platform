import { useState, useEffect } from 'react'
import { emissionsAPI, NormalizedEmissionRecord } from '../api/emissions'

export default function ReviewQueuePage() {
  const [records, setRecords] = useState<NormalizedEmissionRecord[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedRecord, setSelectedRecord] = useState<NormalizedEmissionRecord | null>(null)
  const [showRejectModal, setShowRejectModal] = useState(false)
  const [rejectReason, setRejectReason] = useState('')

  useEffect(() => {
    loadReviewQueue()
  }, [])

  const loadReviewQueue = async () => {
    setIsLoading(true)
    try {
      const response = await emissionsAPI.getReviewQueue()
      setRecords(response.data.results)
    } catch (error) {
      console.error('Failed to load review queue:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleApprove = async (recordId: string) => {
    try {
      await emissionsAPI.approve(recordId, 'Approved by analyst')
      await loadReviewQueue()
      setSelectedRecord(null)
    } catch (error) {
      console.error('Failed to approve record:', error)
    }
  }

  const handleReject = async (recordId: string) => {
    const reason = rejectReason.trim()
    if (!reason) {
      alert('Please enter a rejection reason')
      return
    }

    try {
      await emissionsAPI.reject(recordId, reason)
      await loadReviewQueue()
      setSelectedRecord(null)
      setShowRejectModal(false)
      setRejectReason('')
    } catch (error) {
      console.error('Failed to reject record:', error)
    }
  }

  const getSeverityColor = (severity: string) => {
    if (severity === 'critical') return 'bg-red-100 text-red-800'
    if (severity === 'warning') return 'bg-yellow-100 text-yellow-800'
    return 'bg-blue-100 text-blue-800'
  }

  if (isLoading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="grid grid-cols-3 gap-6">
      {/* List */}
      <div className="col-span-2">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Review Queue</h1>
        <div className="card">
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Category</th>
                  <th>Quantity</th>
                  <th>Period</th>
                  <th>Anomalies</th>
                </tr>
              </thead>
              <tbody>
                {records.map((record) => (
                  <tr
                    key={record.id}
                    onClick={() => setSelectedRecord(record)}
                    className="hover:bg-gray-50 cursor-pointer"
                  >
                    <td className="font-medium">{record.emission_source}</td>
                    <td className="text-sm">{record.emission_category}</td>
                    <td className="text-sm">
                      {record.quantity} {record.unit}
                    </td>
                    <td className="text-sm text-gray-600">
                      {new Date(record.period_start).toLocaleDateString()}
                    </td>
                    <td>
                      {record.anomalies.length > 0 && (
                        <span className="badge badge-warning text-xs">
                          {record.anomalies.length}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Detail Panel */}
      {selectedRecord && (
        <div className="card sticky top-6 h-fit">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-lg font-semibold">{selectedRecord.emission_source}</h2>
            <button
              onClick={() => setSelectedRecord(null)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="space-y-3 mb-4 pb-4 border-b border-gray-200">
            <div>
              <p className="text-xs text-gray-600">Quantity</p>
              <p className="font-semibold">{selectedRecord.quantity} {selectedRecord.unit}</p>
            </div>
            <div>
              <p className="text-xs text-gray-600">CO2e Emissions</p>
              <p className="font-semibold text-blue-600">
                {Number(selectedRecord.emissions_kg_co2e).toFixed(2)} kg CO2e
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-600">Period</p>
              <p className="text-sm">{selectedRecord.period_start} to {selectedRecord.period_end}</p>
            </div>
          </div>

          {selectedRecord.anomalies.length > 0 && (
            <div className="mb-4 pb-4 border-b border-gray-200">
              <p className="text-sm font-semibold mb-2">Anomalies</p>
              <div className="space-y-2">
                {selectedRecord.anomalies.map((anomaly) => (
                  <div key={anomaly.id} className={`p-2 rounded text-xs ${getSeverityColor(anomaly.severity)}`}>
                    <p className="font-semibold">{anomaly.anomaly_type}</p>
                    <p>{anomaly.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={() => handleApprove(selectedRecord.id)}
              className="btn btn-success flex-1"
            >
              Approve
            </button>
            <button
              onClick={() => setShowRejectModal(true)}
              className="btn btn-danger flex-1"
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && selectedRecord && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 shadow-lg">
            <h3 className="text-lg font-semibold mb-4">Reject Record</h3>
            <p className="text-gray-600 mb-4">
              Record: {selectedRecord.emission_source}
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Enter rejection reason..."
              className="w-full border border-gray-300 rounded-lg p-2 mb-4 h-24"
            />
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setShowRejectModal(false)
                  setRejectReason('')
                }}
                className="btn btn-outline flex-1"
              >
                Cancel
              </button>
              <button
                onClick={() => handleReject(selectedRecord.id)}
                className="btn btn-danger flex-1"
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
