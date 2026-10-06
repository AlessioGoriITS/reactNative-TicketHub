import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export function AppLayout() {
  const { session, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const isCustomer = session?.user.role === 'customer'
  const pageName = location.pathname === '/'
    ? 'Panoramica'
    : location.pathname === '/tickets/new'
      ? 'Nuova richiesta'
      : location.pathname.startsWith('/tickets/')
        ? 'Dettaglio ticket'
        : 'Ticket'
  const roleName = session?.user.role === 'customer' ? 'Cliente' : session?.user.role === 'admin' ? 'Amministratore' : 'Operatore'

  const signOut = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink className="brand" to="/" aria-label="TicketHub dashboard">
          <span className="brand-mark" aria-hidden="true">T</span>
          <span className="brand-copy"><strong>TicketHub</strong><small>Support workspace</small></span>
        </NavLink>
        <nav className="main-nav" aria-label="Navigazione principale">
          <p className="nav-label">Workspace</p>
          <NavLink end to="/"><span aria-hidden="true">⌂</span> Panoramica</NavLink>
          <NavLink to="/tickets" className={({ isActive }) => isActive && location.pathname !== '/tickets/new' ? 'active' : ''} aria-current={location.pathname === '/tickets/new' ? false : undefined}><span aria-hidden="true">▤</span> Ticket</NavLink>
          {isCustomer && <NavLink to="/tickets/new"><span aria-hidden="true">＋</span> Nuovo ticket</NavLink>}
        </nav>
        <div className="account-panel">
          <div className="avatar" aria-hidden="true">
            {session?.user.name.slice(0, 1).toUpperCase()}
          </div>
          <div className="account-copy">
            <strong>{session?.user.name}</strong>
            <span>{roleName}</span>
          </div>
          <button className="icon-button" type="button" onClick={signOut} aria-label="Esci">
            ↗
          </button>
        </div>
      </aside>
      <div className="content-shell">
        <header className="mobile-header">
          <span className="brand-mark">T</span>
          <span><strong>TicketHub</strong><small>{pageName}</small></span>
          <button className="text-button" type="button" onClick={signOut}>
            Esci
          </button>
        </header>
        <header className="workspace-header">
          <div className="workspace-context">
            <span>TicketHub <b>/</b> {pageName}</span>
            <strong>{pageName}</strong>
          </div>
          <div className="workspace-actions">
            <span className="ai-status"><i aria-hidden="true" />Gestione richieste attiva</span>
            <div className="header-user"><span className="avatar" aria-hidden="true">{session?.user.name.slice(0, 1).toUpperCase()}</span><span>{session?.user.name}</span></div>
          </div>
        </header>
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
