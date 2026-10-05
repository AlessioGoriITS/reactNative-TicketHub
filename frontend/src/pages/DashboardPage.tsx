import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { ErrorState, LoadingState } from '../components/Feedback'
import { PriorityBadge, StatusBadge } from '../components/TicketBadges'
import type { PaginatedTickets, Ticket } from '../types'

function formatDate(value: string) {
  return new Intl.DateTimeFormat('it-IT', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value))
}

export function DashboardPage() {
  const { session } = useAuth()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const isCustomer = session?.user.role === 'customer'

  useEffect(() => {
    let active = true
    apiRequest<PaginatedTickets>('/tickets?page_size=100', { token: session?.token })
      .then((response) => {
        if (active) setTickets(response.items)
      })
      .catch((requestError) => {
        if (active) setError(getErrorMessage(requestError))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [session?.token])

  const metrics = useMemo(
    () => ({
      open: tickets.filter((ticket) => ['open', 'in_progress', 'waiting_for_customer'].includes(ticket.status)).length,
      urgent: tickets.filter((ticket) => ticket.priority === 'urgent').length,
      resolved: tickets.filter((ticket) => ticket.status === 'resolved').length,
    }),
    [tickets],
  )

  if (loading) return <LoadingState label="Caricamento della dashboard…" />
  if (error) return <ErrorState message={error} />

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div>
          <p className="eyebrow">PANORAMICA</p>
          <h1>{isCustomer ? 'Le tue richieste' : 'Centro operativo'}</h1>
          <p className="muted">{isCustomer ? 'Tieni traccia dello stato delle richieste aperte.' : 'Una vista rapida sul lavoro di assistenza.'}</p>
        </div>
        {isCustomer && <Link className="button button-primary" to="/tickets/new">Apri ticket</Link>}
      </div>

      <div className="metric-grid">
        <article className="metric-card"><span>Ticket visibili</span><strong>{tickets.length}</strong><small>Totale richieste</small></article>
        <article className="metric-card"><span>Da gestire</span><strong>{metrics.open}</strong><small>Aperti o in lavorazione</small></article>
        <article className="metric-card"><span>Urgenti</span><strong>{metrics.urgent}</strong><small>Richiedono attenzione</small></article>
        <article className="metric-card"><span>Risolti</span><strong>{metrics.resolved}</strong><small>In attesa di chiusura</small></article>
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div><h2>Attività recente</h2><p>I ticket aggiornati più di recente.</p></div>
          <Link className="text-link" to="/tickets">Vedi tutti →</Link>
        </div>
        {tickets.length === 0 ? (
          <div className="empty-state"><h3>Nessun ticket da mostrare</h3><p>{isCustomer ? 'Apri un ticket per richiedere assistenza.' : 'I nuovi ticket compariranno qui.'}</p></div>
        ) : (
          <div className="ticket-table" role="table">
            <div className="ticket-row ticket-header" role="row"><span>Ticket</span><span>Stato</span><span>Priorità</span><span>Aggiornato</span></div>
            {tickets.slice(0, 6).map((ticket) => (
              <Link className="ticket-row" role="row" to={`/tickets/${ticket.id}`} key={ticket.id}>
                <span><strong>{ticket.ticket_number}</strong><small>{ticket.title}</small></span>
                <StatusBadge status={ticket.status} />
                <PriorityBadge priority={ticket.priority} />
                <span>{formatDate(ticket.updated_at)}</span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}
