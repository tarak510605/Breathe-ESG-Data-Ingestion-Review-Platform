import { apiClient } from './client'

export interface IngestionJob {
  id: string
  data_source: string
  data_source_name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  file_name: string
  file_size: number
  total_records: number
  valid_records: number
  invalid_records: number
  suspicious_records: number
  processed_at?: string
  processing_error?: string
  created_at: string
}

export const ingestionAPI = {
  upload: (dataSourceId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('data_source_id', dataSourceId)
    return apiClient.post<IngestionJob>(
      '/ingestion-jobs/upload/',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
  },

  listJobs: (page = 1) =>
    apiClient.get<{results: IngestionJob[]; count: number}>(`/ingestion-jobs/?page=${page}`),

  getJob: (jobId: string) =>
    apiClient.get<IngestionJob>(`/ingestion-jobs/${jobId}/`),

  reprocess: (jobId: string) =>
    apiClient.post(`/ingestion-jobs/${jobId}/reprocess/`, {}),

  getErrorSummary: (jobId: string) =>
    apiClient.get(`/ingestion-jobs/${jobId}/error-summary/`),
}
