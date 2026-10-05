# TicketHub

TicketHub è una piattaforma web per la gestione professionale dei ticket di assistenza clienti. Permette a clienti, operatori e amministratori di seguire il ciclo di vita di una richiesta, dalla sua apertura alla risoluzione.

> Stato: struttura iniziale del monorepo. Le funzionalità applicative vengono implementate progressivamente secondo il [piano di progetto](./PIANO_PROGETTO_TICKETHUB.md).

## Architettura

```text
Browser → frontend (React) → backend (FastAPI) → PostgreSQL
                                  │
                                  └→ provider AI configurabile (fase successiva)
```

| Servizio | Tecnologia | Porta predefinita |
| --- | --- | --- |
| Frontend web | React + TypeScript + Vite | 5173 |
| API | FastAPI + Python | 8000 |
| Database | PostgreSQL 16 | 5432 |

## Avvio locale con Docker

### Prerequisiti

- Docker Desktop con Docker Compose v2;
- una porta locale libera per ciascuno dei servizi indicati sopra.

### Configurazione

1. Copiare `.env.example` in `.env`.
2. Sostituire le password di sviluppo se necessario.
3. Avviare lo stack:

   ```bash
   docker compose up --build
   ```

4. Attendere che i healthcheck di database, API e frontend risultino `healthy`, quindi aprire:

   - frontend: `http://localhost:5173`;
   - API: `http://localhost:8000`;
   - documentazione OpenAPI: `http://localhost:8000/docs`;
   - health check: `http://localhost:8000/health`.

Per fermare i servizi, usare `docker compose down`. Il volume PostgreSQL viene mantenuto; per rimuoverlo esplicitamente si può usare `docker compose down -v`.

In alternativa, se `make` è disponibile, sono inclusi i comandi `make up`, `make down`, `make logs`, `make build` e `make test`.

## Struttura del repository

```text
.
├── backend/                 # API FastAPI e logica di dominio
├── frontend/                # applicazione React
├── database/                # migrazioni, seed e note sul database
├── docs/                    # documentazione tecnica e risorse della demo
├── docker-compose.yml       # avvio dell'intero stack
├── .env.example             # variabili da configurare localmente
└── PIANO_PROGETTO_TICKETHUB.md
```

## Sviluppo senza Docker

Il supporto al flusso locale completo sarà documentato insieme a migrazioni e seed del database. Per ora è possibile verificare la base del backend con Docker e l’endpoint `GET /health`.

## Sicurezza delle configurazioni

Non inserire chiavi API, password reali o file `.env` nel repository. Usare esclusivamente `.env.example` come modello per le configurazioni locali.

## Licenza

Questo progetto è distribuito secondo i termini presenti nel file [LICENSE](./LICENSE).
