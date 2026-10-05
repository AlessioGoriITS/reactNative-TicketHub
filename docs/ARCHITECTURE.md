# Architettura TicketHub

## Componenti

```text
┌──────────────────┐       HTTP/JSON        ┌───────────────────┐
│ React frontend   │ ─────────────────────► │ FastAPI backend   │
│ Porta 5173       │ ◄───────────────────── │ Porta 8000        │
└──────────────────┘       JWT bearer       └─────────┬─────────┘
                                                       │ SQLAlchemy
                                                       ▼
                                             ┌───────────────────┐
                                             │ PostgreSQL 16     │
                                             │ Porta 5432        │
                                             └───────────────────┘
                                                       │
                              ┌────────────────────────┴────────────────────┐
                              ▼                                             ▼
                   OpenAI-compatible API                          Ollama opzionale
                   (servizio esterno)                             (profilo Docker)
```

## Backend

Il backend è diviso per responsabilità:

- `api/routes`: endpoint HTTP;
- `api/deps`: sessione database, JWT e autorizzazioni;
- `models`: persistenza SQLAlchemy;
- `schemas`: validazione Pydantic dei payload;
- `services`: audit trail e integrazione AI;
- `db`: configurazione engine, migrazioni e seed.

L’API viene esposta sotto il prefisso `/api`; `/health` resta indipendente dall’autenticazione per i healthcheck.

## Autorizzazione

| Operazione | Cliente | Operatore | Amministratore |
| --- | :---: | :---: | :---: |
| Aprire ticket | ✓ | — | — |
| Vedere ticket propri | ✓ | ✓ | ✓ |
| Vedere tutti i ticket | — | ✓ | ✓ |
| Aggiungere nota interna | — | ✓ | ✓ |
| Assegnare o risolvere | — | ✓ | ✓ |
| Chiudere definitivamente | — | — | ✓ |
| Gestire utenti e categorie | — | — | ✓ |

La verifica avviene sempre nel backend. Il frontend modifica soltanto l’esperienza utente, non le autorizzazioni effettive.

## Persistenza

Le entità principali sono:

```text
users ──< tickets (customer_id)
users ──< tickets (assigned_to_id)
categories ──< tickets
tickets ──< ticket_messages ──> users
tickets ──< attachments
tickets ──< audit_logs
users ──< audit_logs
```

Le migrazioni sono versionate in `backend/alembic/versions/`. Il backend esegue `alembic upgrade head` e il seed demo all’avvio Docker.

## Integrazione AI

Gli endpoint AI sono riservati a operatori e amministratori. L’applicazione invia al provider solo titolo e descrizione del ticket e restituisce un output JSON strutturato. Il risultato resta una proposta: l’operatore decide se applicarlo o inviarlo.

Quando il provider manca o restituisce un errore, il servizio usa un fallback deterministico e inserisce una nota esplicativa nella risposta API. Questo evita che un errore esterno blocchi la gestione dei ticket.
