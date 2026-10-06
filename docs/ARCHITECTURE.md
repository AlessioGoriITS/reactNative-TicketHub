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
                                                       │ HTTP/JSON
                                                       ▼
                                             ┌───────────────────┐
                                             │ Ollama locale     │
                                             │ llama3.2:1b       │
                                             └───────────────────┘
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

Ollama è un servizio Docker incluso nello stack standard. Al primo avvio il job `ollama-init` scarica il modello `llama3.2:1b` nel volume persistente `ollama_data` e ritenta automaticamente se il registry non è momentaneamente raggiungibile. Il backend non resta bloccato dal download: avvia l’applicazione e usa il fallback finché il modello non è pronto.

Alla creazione di un ticket il cliente invia soltanto descrizione e categoria facoltativa. Il backend chiede a Ollama un JSON strutturato e salva titolo, priorità e sintesi prima di restituire il ticket. Il payload non accetta `title` o `priority`, e il backend impedisce ai clienti di modificarli in seguito.

Gli endpoint AI per gli operatori restano disponibili per ricalcolare la sintesi e creare bozze di risposta. Se Ollama non risponde, un fallback deterministico consente comunque di aprire il ticket e l’audit log segnala che l’output non è stato generato dal modello.
