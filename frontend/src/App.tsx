const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

function App() {
  return (
    <main className="landing-page">
      <section className="landing-card" aria-labelledby="app-title">
        <p className="eyebrow">CUSTOMER SUPPORT PLATFORM</p>
        <h1 id="app-title">TicketHub</h1>
        <p className="intro">
          La piattaforma per gestire richieste di assistenza in modo semplice, tracciabile e professionale.
        </p>
        <div className="status" role="status">
          <span aria-hidden="true" className="status-dot" />
          Ambiente inizializzato — API configurata su {apiBaseUrl}
        </div>
      </section>
    </main>
  )
}

export default App
