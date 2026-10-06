import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { ErrorState, LoadingState } from '../components/Feedback'
import { PriorityBadge, StatusBadge } from '../components/TicketBadges'
import type { DashboardSummary, PaginatedTickets, Ticket } from '../types'

function formatDate(value: string) {
  return new Intl.DateTimeFormat('it-IT', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value))
}

export function DashboardPage() {
  const { session } = useAuth()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const isCustomer = session?.user.role === 'customer'

  useEffect(() => {
    let active = true
    Promise.all([
      apiRequest<PaginatedTickets>('/tickets?page_size=100', { token: session?.token }),
      apiRequest<DashboardSummary>('/dashboard/summary', { token: session?.token }),
    ])
      .then(([ticketsResponse, summaryResponse]) => {
        if (active) {
          setTickets(ticketsResponse.items)
          setSummary(summaryResponse)
        }
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

  if (loading) return <LoadingState label="Caricamento della dashboard…" />
  if (error) return <ErrorState message={error} />

  const metrics = [
    { label: 'Ticket visibili', value: summary?.total_tickets ?? 0, detail: 'Totale richieste', icon: '▤', tone: 'blue' },
    { label: 'Da gestire', value: (summary?.open_tickets ?? 0) + (summary?.in_progress_tickets ?? 0), detail: 'Aperti o in lavorazione', icon: '◌', tone: 'amber' },
    { label: 'Urgenti', value: summary?.urgent_tickets ?? 0, detail: 'Richiedono attenzione', icon: '!', tone: 'rose' },
    { label: isCustomer ? 'Risolti' : 'Non assegnati', value: isCustomer ? (summary?.resolved_tickets ?? 0) : (summary?.unassigned_tickets ?? 0), detail: isCustomer ? 'In attesa di chiusura' : 'Da assegnare al supporto', icon: isCustomer ? '✓' : '→', tone: 'mint' },
  ]

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
        {metrics.map((metric) => <article className={`metric-card metric-${metric.tone}`} key={metric.label}><span className="metric-icon" aria-hidden="true">{metric.icon}</span><div><span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.detail}</small></div></article>)}
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
