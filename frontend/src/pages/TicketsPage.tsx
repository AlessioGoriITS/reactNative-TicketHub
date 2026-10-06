import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { apiRequest, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { ErrorState, LoadingState } from '../components/Feedback'
import { PriorityBadge, StatusBadge, statusLabels } from '../components/TicketBadges'
import type { PaginatedTickets, TicketPriority, TicketStatus } from '../types'

const priorities: TicketPriority[] = ['low', 'medium', 'high', 'urgent']
const statuses: TicketStatus[] = ['open', 'in_progress', 'waiting_for_customer', 'resolved', 'closed']

export function TicketsPage() {
  const { session } = useAuth()
  const [data, setData] = useState<PaginatedTickets | null>(null)
  const [status, setStatus] = useState<TicketStatus | ''>('')
  const [priority, setPriority] = useState<TicketPriority | ''>('')
  const [search, setSearch] = useState('')
  const [submittedSearch, setSubmittedSearch] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const isCustomer = session?.user.role === 'customer'

  useEffect(() => {
    let active = true
    setLoading(true)
    const parameters = new URLSearchParams({ page_size: '100' })
    if (status) parameters.set('status', status)
    if (priority) parameters.set('priority', priority)
    if (submittedSearch) parameters.set('search', submittedSearch)
    apiRequest<PaginatedTickets>(`/tickets?${parameters.toString()}`, { token: session?.token })
      .then((response) => {
        if (active) setData(response)
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
  }, [priority, session?.token, status, submittedSearch])

  const submitSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmittedSearch(search.trim())
  }

  return (
    <section className="page-stack">
      <div className="page-heading">
        <div><p className="eyebrow">GESTIONE TICKET</p><h1>{isCustomer ? 'I tuoi ticket' : 'Tutti i ticket'}</h1><p className="muted">Cerca, filtra e consulta lo stato delle richieste.</p></div>
        {isCustomer && <Link className="button button-primary" to="/tickets/new">Apri ticket</Link>}
      </div>

      <section className="filter-bar" aria-label="Filtri ticket">
        <form onSubmit={submitSearch} className="search-field">
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Cerca per titolo o codice" aria-label="Cerca ticket" />
          <button className="button button-secondary" type="submit">Cerca</button>
        </form>
        <label>Stato<select value={status} onChange={(event) => setStatus(event.target.value as TicketStatus | '')}><option value="">Tutti gli stati</option>{statuses.map((item) => <option value={item} key={item}>{statusLabels[item]}</option>)}</select></label>
        <label>Priorità<select value={priority} onChange={(event) => setPriority(event.target.value as TicketPriority | '')}><option value="">Tutte le priorità</option>{priorities.map((item) => <option value={item} key={item}>{item === 'low' ? 'Bassa' : item === 'medium' ? 'Media' : item === 'high' ? 'Alta' : 'Urgente'}</option>)}</select></label>
      </section>

      {loading && <LoadingState label="Caricamento ticket…" />}
      {error && <ErrorState message={error} />}
      {!loading && !error && data && (
        <section className="panel ticket-list-panel">
          <div className="panel-heading"><div><h2>{data.total} ticket</h2><p>Risultati disponibili con i filtri correnti.</p></div></div>
          {data.items.length === 0 ? (
            <div className="empty-state"><h3>Nessun risultato</h3><p>Prova a modificare i filtri oppure apri un nuovo ticket.</p></div>
          ) : (
            <div className="ticket-table" role="table">
              <div className="ticket-row ticket-header" role="row"><span>Ticket</span><span>Prodotto</span><span>Stato</span><span>Priorità</span><span>Assegnato a</span></div>
              {data.items.map((ticket) => (
                <Link className="ticket-row" role="row" to={`/tickets/${ticket.id}`} key={ticket.id}>
                  <span><strong>{ticket.ticket_number}</strong><small>{ticket.title}</small></span>
                  <span>{ticket.product?.name ?? '—'}</span>
                  <StatusBadge status={ticket.status} />
                  <PriorityBadge priority={ticket.priority} />
                  <span>{ticket.assigned_to?.name ?? 'Non assegnato'}</span>
                </Link>
              ))}
            </div>
          )}
        </section>
      )}
    </section>
  )
}
