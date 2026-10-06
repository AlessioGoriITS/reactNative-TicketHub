export type UserRole = 'customer' | 'agent' | 'admin'
export type TicketStatus = 'open' | 'in_progress' | 'waiting_for_customer' | 'resolved' | 'closed'
export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent'

export interface User {
  id: number
  name: string
  email: string
  role: UserRole
  is_active?: boolean
  created_at?: string
}

export interface Category {
  id: number
  name: string
  description: string | null
  is_active?: boolean
}

export interface Product {
  id: number
  code: string
  name: string
  description: string | null
  is_active?: boolean
}

export interface TicketMessage {
  id: number
  body: string
  is_internal: boolean
  created_at: string
  author: User
}

export interface Ticket {
  id: number
  ticket_number: string
  title: string
  description?: string
  status: TicketStatus
  priority: TicketPriority
  category: Category | null
  product: Product | null
  customer: User
  assigned_to: User | null
  created_at: string
  updated_at: string
  resolved_at?: string | null
  ai_summary?: string | null
  ai_suggested_priority?: TicketPriority | null
  messages?: TicketMessage[]
}

export interface PaginatedTickets {
  items: Ticket[]
  total: number
  page: number
  page_size: number
}

export interface DashboardSummary {
  total_tickets: number
  open_tickets: number
  in_progress_tickets: number
  urgent_tickets: number
  resolved_tickets: number
  unassigned_tickets: number
  average_resolution_hours: number | null
}

export interface AuthResponse {
  access_token: string
  token_type: 'bearer'
  user: User
}
