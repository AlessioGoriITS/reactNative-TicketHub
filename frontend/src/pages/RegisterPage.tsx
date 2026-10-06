import { FormEvent, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'

import { apiRequest, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { AuthResponse } from '../types'

export function RegisterPage() {
  const { session, setSession } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
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
      const response = await apiRequest<AuthResponse>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ name, email, password }),
      })
      setSession(response)
      navigate('/', { replace: true })
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
        <div className="auth-visual-copy"><p>Richieste chiare, risposte migliori.</p><span>Segui ogni aggiornamento in un unico spazio sicuro.</span></div>
        <div className="auth-stat"><strong>Supporto organizzato</strong><span>Dal primo messaggio alla risoluzione</span></div>
      </div>
      <div className="auth-card-wrap">
        <form className="auth-card" onSubmit={submit}>
          <p className="eyebrow">NUOVO ACCOUNT</p>
          <h1>Crea il tuo spazio</h1>
          <p className="muted">Registrati per aprire e seguire le tue richieste di assistenza.</p>
          {error && <p className="form-error" role="alert">{error}</p>}
          <label>
            Nome e cognome
            <input value={name} onChange={(event) => setName(event.target.value)} minLength={2} required autoComplete="name" />
          </label>
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required autoComplete="new-password" />
          </label>
          <button className="button button-primary button-full" disabled={submitting} type="submit">
            {submitting ? 'Creazione in corso…' : 'Crea account'}
          </button>
          <p className="auth-switch">Hai già un account? <Link to="/login">Accedi</Link></p>
        </form>
      </div>
    </section>
  )
}
