import { FormEvent, useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { apiRequest, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { Category, Ticket, TicketPriority } from '../types'

export function NewTicketPage() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [categories, setCategories] = useState<Category[]>([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [priority, setPriority] = useState<TicketPriority>('medium')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    apiRequest<Category[]>('/categories', { token: session?.token })
      .then(setCategories)
      .catch((requestError) => setError(getErrorMessage(requestError)))
  }, [session?.token])

  if (session?.user.role !== 'customer') return <Navigate to="/tickets" replace />

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const ticket = await apiRequest<Ticket>('/tickets', {
        method: 'POST',
        token: session.token,
        body: JSON.stringify({
          title,
          description,
          priority,
          ...(categoryId ? { category_id: Number(categoryId) } : {}),
        }),
      })
      navigate(`/tickets/${ticket.id}`)
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="page-stack narrow-page">
      <div className="page-heading"><div><p className="eyebrow">NUOVA RICHIESTA</p><h1>Come possiamo aiutarti?</h1><p className="muted">Descrivi il problema in modo dettagliato: il team saprà intervenire più rapidamente.</p></div></div>
      <form className="panel form-panel" onSubmit={submit}>
        {error && <p className="form-error" role="alert">{error}</p>}
        <label>Oggetto<input value={title} onChange={(event) => setTitle(event.target.value)} minLength={5} maxLength={200} placeholder="Es. Non riesco ad accedere al portale" required /></label>
        <label>Descrizione<textarea value={description} onChange={(event) => setDescription(event.target.value)} minLength={10} maxLength={10_000} placeholder="Indica cosa stavi facendo, cosa ti aspettavi e che cosa è accaduto." rows={7} required /></label>
        <div className="form-grid">
          <label>Categoria<select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}><option value="">Non specificata</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
          <label>Priorità<select value={priority} onChange={(event) => setPriority(event.target.value as TicketPriority)}><option value="low">Bassa</option><option value="medium">Media</option><option value="high">Alta</option><option value="urgent">Urgente</option></select></label>
        </div>
        <div className="form-actions"><button className="button button-primary" type="submit" disabled={submitting}>{submitting ? 'Invio in corso…' : 'Invia ticket'}</button></div>
      </form>
    </section>
  )
}
