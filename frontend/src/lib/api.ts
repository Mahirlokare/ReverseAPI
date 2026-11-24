import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { getAuthTokens, setAuthTokens, clearAuthTokens } from './auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const tokens = getAuthTokens()
    if (tokens?.access_token) {
      config.headers.Authorization = `Bearer ${tokens.access_token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const tokens = getAuthTokens()
        if (tokens?.refresh_token) {
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: tokens.refresh_token,
          })
          const { access_token, refresh_token } = response.data
          setAuthTokens({ access_token, refresh_token })
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        clearAuthTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export { api }
export default api