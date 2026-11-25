import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthTokens {
  access_token: string
  refresh_token: string
}

export interface User {
  id: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
}

interface AuthState {
  tokens: AuthTokens | null
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  setTokens: (tokens: AuthTokens | null) => void
  setUser: (user: User | null) => void
  logout: () => void
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      tokens: null,
      user: null,
      isAuthenticated: false,
      isLoading: true,
      setTokens: (tokens) =>
        set({
          tokens,
          isAuthenticated: !!tokens?.access_token,
        }),
      setUser: (user) =>
        set((state) => ({
          user,
          isAuthenticated: state.isAuthenticated || !!user,
        })),
      logout: () =>
        set({
          tokens: null,
          user: null,
          isAuthenticated: false,
          isLoading: false,
        }),
      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        tokens: state.tokens,
        user: state.user,
        isAuthenticated: !!state.tokens?.access_token,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.isAuthenticated = !!state.tokens?.access_token
          state.isLoading = false
        }
      },
    }
  )
)

export function getAuthTokens(): AuthTokens | null {
  return useAuthStore.getState().tokens
}

export function setAuthTokens(tokens: AuthTokens | null): void {
  useAuthStore.getState().setTokens(tokens)
}

export function clearAuthTokens(): void {
  useAuthStore.getState().logout()
}
