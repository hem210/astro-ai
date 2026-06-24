import { createContext, useContext, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { api, setAccessToken } from '@/api/client'

interface User {
  id: string
  email: string
  name: string
}

interface AuthState {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, name: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const didRunRef = useRef(false)

  // On app load: try to restore session from the HttpOnly refresh cookie.
  // Guarded against StrictMode's dev-only double-invoke — firing this twice
  // would send two concurrent /auth/refresh calls against the same single-use
  // refresh token, and the loser of that race would 401 and log the user out.
  useEffect(() => {
    if (didRunRef.current) return
    didRunRef.current = true

    api.post<{ access_token: string }>('/auth/refresh')
      .then(({ data }) => {
        setAccessToken(data.access_token)
        return api.get<User>('/profile')
      })
      .then(({ data }) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [])

  async function login(email: string, password: string) {
    const { data } = await api.post<{ access_token: string }>('/auth/login', { email, password })
    setAccessToken(data.access_token)
    const { data: profile } = await api.get<User>('/profile')
    setUser(profile)
  }

  async function signup(email: string, name: string, password: string) {
    const { data } = await api.post<{ access_token: string }>('/auth/signup', { email, name, password })
    setAccessToken(data.access_token)
    const { data: profile } = await api.get<User>('/profile')
    setUser(profile)
  }

  async function logout() {
    await api.post('/auth/logout').catch(() => {})
    setAccessToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
