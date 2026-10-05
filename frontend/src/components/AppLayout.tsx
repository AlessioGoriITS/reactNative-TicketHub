import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export function AppLayout() {
  const { session, logout } = useAuth()
  const navigate = useNavigate()
  const isCustomer = session?.user.role === 'customer'

  const signOut = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink className="brand" to="/" aria-label="TicketHub dashboard">
          <span className="brand-mark">T</span>
          <span>TicketHub</span>
        </NavLink>
        <nav className="main-nav" aria-label="Navigazione principale">
          <NavLink end to="/">Dashboard</NavLink>
          <NavLink to="/tickets">Ticket</NavLink>
          {isCustomer && <NavLink to="/tickets/new">Apri ticket</NavLink>}
        </nav>
        <div className="account-panel">
          <div className="avatar" aria-hidden="true">
            {session?.user.name.slice(0, 1).toUpperCase()}
          </div>
          <div className="account-copy">
            <strong>{session?.user.name}</strong>
            <span>{session?.user.role === 'customer' ? 'Cliente' : 'Supporto'}</span>
          </div>
          <button className="icon-button" type="button" onClick={signOut} aria-label="Esci">
            ↗
          </button>
        </div>
      </aside>
      <div className="content-shell">
        <header className="mobile-header">
          <span className="brand-mark">T</span>
          <strong>TicketHub</strong>
          <button className="text-button" type="button" onClick={signOut}>
            Esci
          </button>
        </header>
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
