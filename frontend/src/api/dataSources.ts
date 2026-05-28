import { apiClient } from './client'

export interface DataSource {
  id: string
  name: string
  source_type: string
  created_at: string
}

export const dataSourcesAPI = {
  list: () =>
    apiClient.get<{ results: DataSource[] }>('/data-sources/'),

  get: (id: string) =>
    apiClient.get<DataSource>(`/data-sources/${id}/`),
}
