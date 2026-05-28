import { apiClient } from './client'

export interface AuditLog {
  id: string
  user_email: string
  action: 'created' | 'edited' | 'approved' | 'rejected' | 'locked' | 'comment_added'
  record_id: string
  record_type: string
  change_reason: string
  created_at: string
}

export const auditAPI = {
  listLogs: (recordId?: string, page = 1) => {
    let url = `/audit-logs/?page=${page}`
    if (recordId) url += `&record_id=${recordId}`
    return apiClient.get<{ results: AuditLog[]; count: number }>(url)
  },

  getLog: (logId: string) =>
    apiClient.get<AuditLog>(`/audit-logs/${logId}/`),
}
