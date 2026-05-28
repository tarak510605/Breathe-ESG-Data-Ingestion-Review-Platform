import { apiClient } from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access: string
  refresh: string
}

export const authAPI = {
  login: (email: string, password: string) =>
    apiClient.post<TokenResponse>('/auth/login/', { email, password }),

  refresh: (refreshToken: string) =>
    apiClient.post<TokenResponse>('/auth/refresh/', { refresh: refreshToken }),

  me: () => apiClient.get('/organizations/me/'),
}
