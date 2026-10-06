import { FormEvent, useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { apiRequest, getErrorMessage } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import type { Product, Ticket } from '../types'

export function NewTicketPage() {
  const { session } = useAuth()
  const navigate = useNavigate()
  const [products, setProducts] = useState<Product[]>([])
  const [productId, setProductId] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    apiRequest<Product[]>('/products', { token: session?.token })
      .then(setProducts)
      .catch((requestError) => setError(getErrorMessage(requestError)))
  }, [session?.token])

  if (session?.user.role !== 'customer') return <Navigate to="/tickets" replace />

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const ticket = await apiRequest<Ticket>('/tickets', {
        method: 'POST',
        token: session.token,
        body: JSON.stringify({
          description,
          product_id: Number(productId),
        }),
      })
      navigate(`/tickets/${ticket.id}`)
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="page-stack narrow-page">
      <div className="page-heading"><div><p className="eyebrow">NUOVA RICHIESTA</p><h1>Come possiamo aiutarti?</h1><p className="muted">Descrivi il problema con più dettagli possibili: penseremo noi a organizzare la richiesta.</p></div></div>
      <form className="panel form-panel" onSubmit={submit}>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="ai-assist-banner"><span className="ai-assist-icon" aria-hidden="true">✦</span><div><strong>Richiesta organizzata automaticamente</strong><p>Seleziona il prodotto interessato: titolo, priorità, sintesi e categoria verranno definiti in base ai dettagli che ci fornisci.</p></div></div>
        <label>Prodotto interessato<select value={productId} onChange={(event) => setProductId(event.target.value)} required><option value="" disabled>Seleziona un prodotto</option>{products.map((product) => <option key={product.id} value={product.id}>{product.name} — {product.description}</option>)}</select></label>
        <label>Descrizione<textarea value={description} onChange={(event) => setDescription(event.target.value)} minLength={10} maxLength={10_000} placeholder="Indica cosa stavi facendo, cosa ti aspettavi e che cosa è accaduto." rows={7} required /></label>
        <div className="form-actions"><button className="button button-primary" type="submit" disabled={submitting}>{submitting ? 'Invio della richiesta…' : 'Invia ticket'}</button></div>
      </form>
    </section>
  )
}
