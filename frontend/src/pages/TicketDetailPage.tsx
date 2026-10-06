import { FormEvent, useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { apiRequest, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { ErrorState, LoadingState } from '../components/Feedback'
import { PriorityBadge, StatusBadge } from '../components/TicketBadges'
import type { Ticket } from '../types'

interface AiReplyResponse {
  reply: string
  source: 'ai' | 'fallback'
  notice: string | null
}

interface AiClassificationResponse {
  source: 'ai' | 'fallback'
  notice: string | null
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('it-IT', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function TicketDetailPage() {
  const { id } = useParams()
  const { session } = useAuth()
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [reply, setReply] = useState('')
  const [internal, setInternal] = useState(false)
  const [error, setError] = useState('')
  const [aiNotice, setAiNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const isStaff = session?.user.role === 'agent' || session?.user.role === 'admin'

  const loadTicket = useCallback(async () => {
    if (!id) return
    setLoading(true)
    try {
      const response = await apiRequest<Ticket>(`/tickets/${id}`, { token: session?.token })
      setTicket(response)
      setError('')
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [id, session?.token])

  useEffect(() => {
    void loadTicket()
  }, [loadTicket])

  const submitMessage = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!ticket || !reply.trim()) return
    setSending(true)
    setError('')
    try {
      await apiRequest(`/tickets/${ticket.id}/messages`, {
        method: 'POST',
        token: session?.token,
        body: JSON.stringify({ body: reply, is_internal: internal }),
      })
      setReply('')
      setInternal(false)
      await loadTicket()
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSending(false)
    }
  }

  const performAction = async (path: string) => {
    if (!ticket) return
    setSending(true)
    setError('')
    try {
      await apiRequest(`/tickets/${ticket.id}/${path}`, { method: 'POST', token: session?.token })
      await loadTicket()
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSending(false)
    }
  }

  const requestAi = async (action: 'classify' | 'suggest-reply') => {
    if (!ticket) return
    setSending(true)
    setError('')
    try {
      if (action === 'classify') {
        const response = await apiRequest<AiClassificationResponse>(`/ai/tickets/${ticket.id}/classify`, { method: 'POST', token: session?.token })
        setAiNotice('Sintesi aggiornata.')
        await loadTicket()
      } else {
        const response = await apiRequest<AiReplyResponse>(`/ai/tickets/${ticket.id}/suggest-reply`, { method: 'POST', token: session?.token })
        setReply(response.reply)
        setInternal(false)
        setAiNotice('Bozza inserita nel messaggio.')
      }
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSending(false)
    }
  }

  if (loading) return <LoadingState label="Caricamento del ticket…" />
  if (error && !ticket) return <ErrorState message={error} />
  if (!ticket) return null

  const canReply = ticket.status !== 'closed'
  const canResolve = isStaff && !['resolved', 'closed'].includes(ticket.status)
  const canReopen = ['resolved', 'closed'].includes(ticket.status)

  return (
    <section className="page-stack ticket-detail-page">
      <Link className="back-link" to="/tickets">← Torna ai ticket</Link>
      {error && <ErrorState message={error} />}
      <section className="panel ticket-hero">
        <div className="ticket-hero-main">
          <p className="ticket-number">{ticket.ticket_number}</p>
          <h1>{ticket.title}</h1>
          <div className="ticket-meta"><StatusBadge status={ticket.status} /><PriorityBadge priority={ticket.priority} />{ticket.category && <span className="category-chip">{ticket.category.name}</span>}{ticket.product && <span className="product-chip">{ticket.product.name}</span>}</div>
        </div>
        <div className="ticket-actions">
          {isStaff && <button className="button button-secondary" type="button" disabled={sending} onClick={() => void requestAi('classify')}>Aggiorna sintesi</button>}
          {canResolve && <button className="button button-primary" type="button" disabled={sending} onClick={() => void performAction('resolve')}>Segna come risolto</button>}
          {canReopen && <button className="button button-secondary" type="button" disabled={sending} onClick={() => void performAction('reopen')}>Riapri ticket</button>}
        </div>
      </section>
      {aiNotice && <p className="feedback loading">{aiNotice}</p>}

      <div className="detail-grid">
        <div className="page-stack">
          <section className="panel ticket-description"><h2>Descrizione</h2><p>{ticket.description}</p></section>
          <section className="panel conversation-panel">
            <div className="panel-heading"><div><h2>Conversazione</h2><p>Messaggi visibili ai partecipanti del ticket.</p></div></div>
            <div className="conversation">
              {!ticket.messages?.length && <div className="empty-state compact"><h3>Ancora nessun messaggio</h3><p>Puoi aggiungere ulteriori dettagli qui sotto.</p></div>}
              {ticket.messages?.map((message) => (
                <article className={`message ${message.is_internal ? 'message-internal' : ''}`} key={message.id}>
                  <div className="message-avatar" aria-hidden="true">{message.author.name.slice(0, 1).toUpperCase()}</div>
                  <div className="message-content"><header><strong>{message.author.name}</strong>{message.is_internal && <span className="internal-label">Nota interna</span>}<time>{formatDateTime(message.created_at)}</time></header><p>{message.body}</p></div>
                </article>
              ))}
            </div>
            {canReply && (
              <form className="reply-form" onSubmit={submitMessage}>
                <label htmlFor="reply">{internal ? 'Nota interna' : 'Risposta'}</label>
                <textarea id="reply" rows={4} value={reply} onChange={(event) => setReply(event.target.value)} placeholder={internal ? 'Questa nota sarà visibile solo agli operatori.' : 'Scrivi un aggiornamento o una risposta…'} required />
                <div className="form-actions reply-actions">
                  {isStaff && <label className="checkbox-label"><input type="checkbox" checked={internal} onChange={(event) => setInternal(event.target.checked)} /> Nota interna</label>}
                  {isStaff && <button className="button button-secondary" type="button" disabled={sending} onClick={() => void requestAi('suggest-reply')}>Suggerisci risposta</button>}
                  <button className="button button-primary" type="submit" disabled={sending || !reply.trim()}>{sending ? 'Invio…' : 'Invia messaggio'}</button>
                </div>
              </form>
            )}
          </section>
        </div>
        <aside className="page-stack">
          <section className="panel metadata-card"><h2>Dettagli</h2><dl><div><dt>Prodotto</dt><dd>{ticket.product?.name ?? 'Non specificato'}</dd></div><div><dt>Cliente</dt><dd>{ticket.customer.name}</dd></div><div><dt>Assegnato a</dt><dd>{ticket.assigned_to?.name ?? 'Non assegnato'}</dd></div><div><dt>Creato il</dt><dd>{formatDateTime(ticket.created_at)}</dd></div><div><dt>Ultimo aggiornamento</dt><dd>{formatDateTime(ticket.updated_at)}</dd></div>{ticket.resolved_at && <div><dt>Risolto il</dt><dd>{formatDateTime(ticket.resolved_at)}</dd></div>}</dl></section>
          {ticket.ai_summary && <section className="panel ai-card"><p className="eyebrow">RIEPILOGO</p><h2>Sintesi della richiesta</h2><p>{ticket.ai_summary}</p></section>}
        </aside>
      </div>
    </section>
  )
}
