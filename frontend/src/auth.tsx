import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { User, UserRole } from './types'

interface AuthState {
  token: string | null
  user: User | null
  role: UserRole | null
  login: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthState>(null!)

function parseJwt(token: string): { sub: string; role: UserRole } | null {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [user, setUser] = useState<User | null>(() => {
    const t = localStorage.getItem('token')
    if (!t) return null
    const payload = parseJwt(t)
    if (!payload) return null
    return { id: Number(payload.sub), email: '', role: payload.role }
  })

  const login = (newToken: string) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
    const payload = parseJwt(newToken)
    if (payload) {
      setUser({ id: Number(payload.sub), email: '', role: payload.role })
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, user, role: user?.role ?? null, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
