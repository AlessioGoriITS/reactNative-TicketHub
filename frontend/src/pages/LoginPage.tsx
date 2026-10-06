import { FormEvent, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { apiRequest, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { AuthResponse } from '../types'

export function LoginPage() {
  const { session, setSession } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (session) return <Navigate to="/" replace />

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const response = await apiRequest<AuthResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setSession(response)
      const target = (location.state as { from?: string } | null)?.from ?? '/'
      navigate(target, { replace: true })
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-visual" aria-hidden="true">
        <span className="brand-mark">T</span>
        <div className="auth-visual-copy"><p>Assistenza chiara, sempre sotto controllo.</p><span>Una workspace professionale per clienti e team di supporto.</span></div>
        <div className="auth-stat"><strong>Gestione intelligente</strong><span>Richieste ordinate e sempre tracciabili</span></div>
      </div>
      <div className="auth-card-wrap">
        <form className="auth-card" onSubmit={submit}>
          <p className="eyebrow">BENTORNATO</p>
          <h1>Accedi a TicketHub</h1>
          <p className="muted">Gestisci le richieste dei tuoi clienti da un unico spazio di lavoro.</p>
          {error && <p className="form-error" role="alert">{error}</p>}
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" />
          </label>
          <button className="button button-primary button-full" disabled={submitting} type="submit">
            {submitting ? 'Accesso in corso…' : 'Accedi'}
          </button>
          <p className="auth-switch">Non hai un account? <Link to="/register">Registrati</Link></p>
        </form>
      </div>
    </section>
  )
}
