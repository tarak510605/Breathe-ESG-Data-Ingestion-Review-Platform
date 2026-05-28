import { create } from 'zustand'
import { authAPI } from '../api/auth'

interface User {
  id: string
  email: string
  role: 'admin' | 'analyst' | 'reviewer'
  organization: string
  first_name?: string
  last_name?: string
}

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await authAPI.login(email, password)
      const { access } = response.data
      localStorage.setItem('access_token', access)
      set({
        token: access,
        isAuthenticated: true,
        isLoading: false,
      })
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Login failed',
        isLoading: false,
      })
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    set({
      user: null,
      token: null,
      isAuthenticated: false,
    })
  },

  setUser: (user: User | null) => set({ user }),
  setToken: (token: string | null) => set({ token, isAuthenticated: !!token }),
}))
