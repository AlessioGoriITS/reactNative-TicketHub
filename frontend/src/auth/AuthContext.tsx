import { createContext, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import type { AuthResponse, User } from '../types'

interface Session {
  token: string
  user: User
}

interface AuthContextValue {
  session: Session | null
  setSession: (response: AuthResponse) => void
  logout: () => void
}

const STORAGE_KEY = 'tickethub.session'
const AuthContext = createContext<AuthContextValue | null>(null)

function readStoredSession(): Session | null {
  try {
    const rawSession = localStorage.getItem(STORAGE_KEY)
    if (!rawSession) return null
    const parsed = JSON.parse(rawSession) as Session
    return parsed.token && parsed.user ? parsed : null
  } catch {
    localStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, updateSession] = useState<Session | null>(readStoredSession)

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      setSession: (response) => {
        const nextSession = { token: response.access_token, user: response.user }
        localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession))
        updateSession(nextSession)
      },
      logout: () => {
        localStorage.removeItem(STORAGE_KEY)
        updateSession(null)
      },
    }),
    [session],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth deve essere usato all’interno di AuthProvider.')
  return context
}
