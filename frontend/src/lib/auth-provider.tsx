import { useEffect } from 'react'
import { useAuthStore, getAuthTokens } from './auth'
import { api } from './api'
import type { User } from './auth'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading, logout } = useAuthStore()

  useEffect(() => {
    let mounted = true

    const initAuth = async () => {
      const storedTokens = getAuthTokens()
      if (storedTokens?.access_token) {
        try {
          const response = await api.get<User>('/auth/me')
          if (mounted) {
            setUser(response.data)
            useAuthStore.setState({ isAuthenticated: true, isLoading: false })
          }
        } catch (error: unknown) {
          const axiosError = error as { response?: { status?: number } }
          if (axiosError?.response?.status === 401) {
            if (mounted) {
              logout()
            }
          }
        }
      }
      if (mounted) {
        setLoading(false)
      }
    }

    initAuth()

    return () => {
      mounted = false
    }
  }, [setUser, setLoading, logout])

  return <>{children}</>
}
