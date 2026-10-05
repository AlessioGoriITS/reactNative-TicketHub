import type { TicketPriority, TicketStatus } from '../types'

const statusLabels: Record<TicketStatus, string> = {
  open: 'Aperto',
  in_progress: 'In lavorazione',
  waiting_for_customer: 'In attesa cliente',
  resolved: 'Risolto',
  closed: 'Chiuso',
}

const priorityLabels: Record<TicketPriority, string> = {
  low: 'Bassa',
  medium: 'Media',
  high: 'Alta',
  urgent: 'Urgente',
}

export function StatusBadge({ status }: { status: TicketStatus }) {
  return <span className={`badge badge-status status-${status}`}>{statusLabels[status]}</span>
}

export function PriorityBadge({ priority }: { priority: TicketPriority }) {
  return <span className={`badge badge-priority priority-${priority}`}>{priorityLabels[priority]}</span>
}

export { priorityLabels, statusLabels }
