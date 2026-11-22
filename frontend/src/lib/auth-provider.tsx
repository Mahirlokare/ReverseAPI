import { useEffect } from 'react'
import { useAuthStore } from './auth'
import { api } from './api'
import type { User } from './auth'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { tokens, setUser, setLoading } = useAuthStore()

  useEffect(() => {
    const initAuth = async () => {
      if (tokens?.access_token) {
        try {
          const response = await api.get<User>('/auth/me')
          setUser(response.data)
        } catch {
          // Token invalid, will be handled by interceptor
        }
      }
      setLoading(false)
    }
    initAuth()
  }, [tokens, setUser, setLoading])

  return <>{children}</>
}