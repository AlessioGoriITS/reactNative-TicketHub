import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return <section className="empty-page"><p className="eyebrow">404</p><h1>Pagina non trovata</h1><p className="muted">L’indirizzo richiesto non esiste o non è più disponibile.</p><Link className="button button-primary" to="/">Torna alla dashboard</Link></section>
}
