import { apiClient } from './client'

export interface NormalizedEmissionRecord {
  id: string
  emission_category: string
  emission_source: string
  quantity: number
  unit: string
  emissions_kg_co2e: number
  period_start: string
  period_end: string
  facility_code?: string
  status: 'pending_review' | 'approved' | 'rejected' | 'flagged'
  review_decision: 'pending' | 'approved' | 'rejected'
  is_locked: boolean
  reviewed_by_email?: string
  review_comment?: string
  anomalies: AnomalyFlag[]
  created_at: string
}

export interface AnomalyFlag {
  id: string
  anomaly_type: string
  severity: 'info' | 'warning' | 'critical'
  description: string
  metric_name?: string
}

export const emissionsAPI = {
  listRecords: (status?: string, category?: string, page = 1) => {
    let url = `/emissions/?page=${page}`
    if (status) url += `&status=${status}`
    if (category) url += `&emission_category=${category}`
    return apiClient.get<{results: NormalizedEmissionRecord[]; count: number}>(url)
  },

  getReviewQueue: (page = 1) =>
    apiClient.get<{results: NormalizedEmissionRecord[]; count: number}>(
      `/emissions/review_queue/?page=${page}`
    ),

  getRecord: (recordId: string) =>
    apiClient.get<NormalizedEmissionRecord>(`/emissions/${recordId}/`),

  approve: (recordId: string, comment = '') =>
    apiClient.post(`/emissions/${recordId}/approve/`, { comment }),

  reject: (recordId: string, reason: string) =>
    apiClient.post(`/emissions/${recordId}/reject/`, { reason }),

  edit: (recordId: string, data: any) =>
    apiClient.patch(`/emissions/${recordId}/`, data),

  getAuditTrail: (recordId: string) =>
    apiClient.get(`/emissions/${recordId}/audit-trail/`),

  listAnomalies: (page = 1) =>
    apiClient.get(`/anomalies/?page=${page}`),

  getUnresolvedAnomalies: (page = 1) =>
    apiClient.get(`/anomalies/unresolved/?page=${page}`),
}
