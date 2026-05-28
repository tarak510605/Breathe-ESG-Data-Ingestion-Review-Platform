import { useState, useEffect } from 'react'
import { ingestionAPI, IngestionJob } from '../api/ingestion'
import { dataSourcesAPI, DataSource } from '../api/dataSources'

export default function IngestionsPage() {
  const [jobs, setJobs] = useState<IngestionJob[]>([])
  const [dataSources, setDataSources] = useState<DataSource[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedDataSource, setSelectedDataSource] = useState<string>('')
  const [isUploading, setIsUploading] = useState(false)

  useEffect(() => {
    loadJobs()
    loadDataSources()
  }, [])

  const loadDataSources = async () => {
    try {
      const response = await dataSourcesAPI.list()
      console.log('Data sources response:', response)
      setDataSources(response.data.results)
    } catch (error) {
      console.error('Failed to load data sources:', error)
    }
  }

  const loadJobs = async () => {
    setIsLoading(true)
    try {
      const response = await ingestionAPI.listJobs()
      setJobs(response.data.results)
    } catch (error) {
      console.error('Failed to load jobs:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile || !selectedDataSource) {
      alert('Please select both a data source and a file')
      return
    }

    setIsUploading(true)
    try {
      await ingestionAPI.upload(selectedDataSource, selectedFile)
      alert('File uploaded successfully!')
      setSelectedFile(null)
      setSelectedDataSource('')
      setShowUpload(false)
      loadJobs() // Refresh the jobs list
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed. Check console for details.')
    } finally {
      setIsUploading(false)
    }
  }

  const getStatusColor = (status: string) => {
    if (status === 'completed') return 'bg-green-100 text-green-800'
    if (status === 'failed') return 'bg-red-100 text-red-800'
    if (status === 'processing') return 'bg-blue-100 text-blue-800'
    return 'bg-yellow-100 text-yellow-800'
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Ingestion Jobs</h1>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="btn btn-primary"
        >
          New Upload
        </button>
      </div>

      {showUpload && (
        <div className="card bg-blue-50 border border-blue-200">
          <h2 className="text-lg font-semibold mb-4">Upload ESG Data</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data Source
              </label>
              <select 
                className="input"
                value={selectedDataSource}
                onChange={(e) => setSelectedDataSource(e.target.value)}
              >
                <option value="">Select a data source...</option>
                {dataSources.map((source) => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                File
              </label>
              <input
                type="file"
                className="input"
                onChange={handleFileChange}
                accept=".csv,.json"
              />
              {selectedFile && (
                <p className="text-sm text-gray-600 mt-1">
                  Selected: {selectedFile.name}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <button 
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={isUploading || !selectedFile || !selectedDataSource}
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </button>
              <button
                onClick={() => {
                  setShowUpload(false)
                  setSelectedFile(null)
                  setSelectedDataSource('')
                }}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Source</th>
                  <th>Status</th>
                  <th>Records</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:cursor-pointer">
                    <td className="font-medium">{job.file_name}</td>
                    <td>{job.data_source_name}</td>
                    <td>
                      <span className={`badge ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                    </td>
                    <td>
                      <div className="text-sm">
                        <p className="font-medium">{job.total_records} total</p>
                        <p className="text-gray-600">
                          {job.valid_records} valid, {job.invalid_records} invalid
                        </p>
                      </div>
                    </td>
                    <td className="text-sm text-gray-600">
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
