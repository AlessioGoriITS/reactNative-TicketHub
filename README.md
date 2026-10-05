# TicketHub

TicketHub è una piattaforma full-stack per la gestione professionale delle richieste di assistenza clienti. Clienti, operatori e amministratori lavorano sullo stesso flusso: apertura, classificazione, conversazione, assegnazione, risoluzione e analisi delle richieste.

Il progetto è un monorepo avviabile in locale tramite Docker Compose. Include database PostgreSQL, API REST documentata, frontend web, autenticazione JWT, ruoli, dati demo, test e una funzionalità AI per classificare i ticket e suggerire risposte modificabili dagli operatori.

## Indice

- [Funzionalità](#funzionalità)
- [Architettura e tecnologie](#architettura-e-tecnologie)
- [Avvio rapido con Docker](#avvio-rapido-con-docker)
- [Account e dati demo](#account-e-dati-demo)
- [Configurazione AI](#configurazione-ai)
- [API principali](#api-principali)
- [Sviluppo locale e test](#sviluppo-locale-e-test)
- [Struttura del repository](#struttura-del-repository)
- [Sicurezza e limiti](#sicurezza-e-limiti)
- [Sviluppi futuri](#sviluppi-futuri)
- [Riferimenti](#riferimenti)

## Funzionalità

### Clienti

- registrazione, login e profilo tramite token JWT;
- apertura di ticket con categoria e priorità;
- ricerca, filtri e storico dei propri ticket;
- conversazione con il supporto;
- riapertura di un ticket risolto;
- dashboard personale con statistiche calcolate dal database.

### Operatori

- visione completa dei ticket e dei loro stati;
- assegnazione a un operatore;
- note interne, invisibili ai clienti;
- risoluzione dei ticket;
- dashboard operativa;
- classificazione AI e suggerimento di risposta, sempre modificabili prima dell’uso.

### Amministratori

- tutte le autorizzazioni degli operatori;
- gestione utenti, ruoli e stato di attivazione;
- creazione e disattivazione delle categorie;
- chiusura definitiva dei ticket.

### Intelligenza artificiale

L’AI è integrata nel backend, non nel browser. Un operatore può:

- ottenere un riassunto del ticket;
- ricevere categoria, priorità e parole chiave suggerite;
- generare una bozza di risposta professionale.

Nessuna risposta viene inviata automaticamente e l’AI non cambia autonomamente priorità, categoria o stato. Se nessun provider è configurato oppure il provider non risponde, le API forniscono un fallback locale esplicitamente identificato: il resto dell’applicazione continua a funzionare.

## Architettura e tecnologie

```text
Browser
   │
   ▼
React + TypeScript + Vite ───────► FastAPI REST API ───────► PostgreSQL 16
                                         │
                                         ├── OpenAI / provider compatibile
                                         └── Ollama locale opzionale
```

| Componente | Tecnologia | Responsabilità |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite, React Router | Interfaccia web responsive e gestione sessione JWT |
| Backend | Python, FastAPI, SQLAlchemy, Alembic | API REST, regole di business, ruoli, audit e AI |
| Database | PostgreSQL 16 | utenti, categorie, ticket, messaggi, allegati e audit log |
| Container | Docker Compose, Nginx | avvio coerente dei servizi e distribuzione del frontend |
| AI | OpenAI-compatible API o Ollama | classificazione e suggerimenti per gli operatori |

Per i dettagli dei flussi e della struttura dei dati, consultare [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Avvio rapido con Docker

### Prerequisiti

- Git;
- Docker Desktop avviato, con Docker Compose v2;
- porte locali `5173`, `8000` e `5432` disponibili.

Non sono richiesti Node.js, Python, PostgreSQL o un provider AI per il percorso standard: i servizi applicativi vengono eseguiti nei container. L’AI usa il fallback locale finché non viene configurato un provider.

### 1. Clonare e configurare

```powershell
git clone <URL-DEL-REPOSITORY> TicketHub
cd TicketHub
Copy-Item .env.example .env
```

Su macOS/Linux usare:

```bash
cp .env.example .env
```

Aprire `.env` e sostituire almeno `POSTGRES_PASSWORD` e `JWT_SECRET_KEY` con valori locali sicuri. Non effettuare il commit di `.env`.

### 2. Avviare tutti i servizi

```bash
docker compose up --build
```

Al primo avvio il backend esegue automaticamente la migrazione Alembic e carica i dati demo. Attendere che i servizi siano `healthy`, quindi aprire:

| Risorsa | Indirizzo |
| --- | --- |
| Applicazione web | <http://localhost:5173> |
| API REST | <http://localhost:8000> |
| Swagger / OpenAPI | <http://localhost:8000/docs> |
| Health check | <http://localhost:8000/health> |

Per arrestare i container:

```bash
docker compose down
```

I dati PostgreSQL sono persistenti. Per rimuoverli e ripartire da zero:

```bash
docker compose down -v
```

Sono disponibili anche i comandi `make up`, `make down`, `make logs`, `make build` e `make test` nei sistemi che includono `make`.

## Account e dati demo

Il seed viene eseguito una sola volta sul database inizialmente vuoto.

| Ruolo | Email | Password |
| --- | --- | --- |
| Amministratore | `admin@tickethub.local` | `TicketHubDemo2026!` |
| Operatore | `operatore@tickethub.local` | `TicketHubDemo2026!` |
| Cliente | `cliente@tickethub.local` | `TicketHubDemo2026!` |

Vengono creati anche quattro categorie, due ticket e messaggi di esempio. Queste credenziali sono esclusivamente per la demo e non devono essere riutilizzate fuori dall’ambiente locale.

## Configurazione AI

Le variabili di configurazione sono in `.env`. Il comportamento predefinito è sicuro e non richiede chiavi:

```env
AI_PROVIDER=none
```

In questa modalità gli endpoint AI rispondono con un fallback locale identificato come `source: "fallback"`.

### OpenAI o API compatibile

Per usare OpenAI:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

Per un provider OpenAI-compatible, ad esempio OpenRouter, impostare `AI_PROVIDER=openai-compatible`, l’URL base e il modello previsti dal provider. Le chiavi restano nel file `.env`, che è ignorato da Git.

### Ollama locale

È incluso un servizio Ollama opzionale, escluso dall’avvio standard per evitare download non richiesti. Per abilitarlo:

```bash
docker compose --profile ollama up --build
docker compose exec ollama ollama pull llama3.2
```

Poi impostare in `.env`:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2
```

Riavviare il backend dopo la modifica della configurazione. Per eseguire Ollama già installato sull’host o su un altro server, impostare `OLLAMA_BASE_URL` sull’indirizzo raggiungibile dal container backend.

## API principali

La documentazione completa e testabile è disponibile in Swagger su `/docs`.

| Area | Endpoint principali |
| --- | --- |
| Sistema | `GET /health`, `GET /api/health` |
| Autenticazione | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| Ticket | `GET/POST /api/tickets`, `GET/PATCH /api/tickets/{id}` |
| Workflow | `POST /api/tickets/{id}/assign`, `/status`, `/resolve`, `/reopen` |
| Messaggi | `GET/POST /api/tickets/{id}/messages` |
| AI | `POST /api/ai/tickets/{id}/classify`, `/suggest-reply` |
| Dashboard | `GET /api/dashboard/summary` |
| Categorie | `GET/POST /api/categories`, `PATCH /api/categories/{id}` |
| Amministrazione | `GET /api/admin/users`, `PATCH /api/admin/users/{id}` |

Gli endpoint autenticati richiedono l’header:

```http
Authorization: Bearer <access_token>
```

## Sviluppo locale e test

Docker Compose è il percorso consigliato perché avvia insieme frontend, backend e PostgreSQL. Per lavorare senza container servono Python 3.13+, Node.js 22+ e un database PostgreSQL raggiungibile.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://<user>:<password>@localhost:5432/tickethub"
alembic upgrade head
python -m app.db.seed
pytest
uvicorn app.main:app --reload
```

Su macOS/Linux sostituire l’attivazione con `source .venv/bin/activate`.

### Frontend

In un secondo terminale:

```bash
cd frontend
npm ci
npm run dev
```

Il frontend cerca l’API in `http://localhost:8000/api`. Per modificarla, creare `frontend/.env.local` con:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

### Controlli eseguiti

```bash
cd backend
pytest

cd ../frontend
npm run build
```

La suite backend copre registrazione, login, token, ruoli, isolamento dei ticket, note interne, assegnazione, risoluzione, dashboard, amministrazione e fallback AI.

## Struttura del repository

```text
.
├── backend/
│   ├── alembic/               # migrazioni versionate
│   ├── app/
│   │   ├── api/               # router, dipendenze e endpoint REST
│   │   ├── db/                # sessione, base ORM e seed demo
│   │   ├── models/            # modelli SQLAlchemy
│   │   ├── schemas/           # validazione input/output Pydantic
│   │   └── services/          # AI e audit log
│   └── tests/                 # test Pytest
├── frontend/
│   └── src/                   # React: pagine, componenti, API client e sessione
├── database/                  # istruzioni relative al database
├── docs/                      # architettura e guida demo
├── docker-compose.yml         # stack completo locale
├── .env.example               # configurazione da copiare in .env
├── Makefile                   # comandi di servizio opzionali
└── PIANO_PROGETTO_TICKETHUB.md
```

## Sicurezza e limiti

- Le password sono memorizzate con hash bcrypt; non vengono mai salvate in chiaro.
- Le API proteggono le operazioni tramite JWT e controlli di ruolo lato backend.
- Le note interne non vengono restituite agli account cliente.
- Le azioni importanti sono registrate in `audit_logs`.
- Il progetto non invia email reali e non carica ancora allegati fisici: la tabella è predisposta ma lo storage non è implementato.
- L’AI può produrre errori o informazioni imprecise: gli output sono solo suggerimenti da verificare dall’operatore.
- Per un deploy reale occorrono HTTPS, secret manager, rate limiting, backup, osservabilità e password/chiavi diverse da quelle demo.

## Sviluppi futuri

- upload di allegati con storage S3-compatible;
- notifiche email e webhook;
- ricerca full-text e knowledge base semantica;
- gestione SLA, escalation e orari lavorativi;
- assegnazione operatore dalla UI e gestione completa delle categorie;
- recupero password e verifica email;
- paginazione e filtri avanzati lato frontend;
- audit log consultabile per gli amministratori;
- test end-to-end e pipeline CI/CD;
- deploy cloud con HTTPS, monitoraggio e backup automatici.

## Riferimenti

- [FastAPI — documentazione ufficiale](https://fastapi.tiangolo.com/)
- [React — documentazione ufficiale](https://react.dev/)
- [PostgreSQL — documentazione ufficiale](https://www.postgresql.org/docs/)
- [Docker Compose — documentazione ufficiale](https://docs.docker.com/compose/)
- [OpenAI API — riferimento ufficiale](https://developers.openai.com/api/reference/resources/chat)
- [Ollama API — documentazione ufficiale](https://docs.ollama.com/api/introduction)

## Licenza

Il progetto è distribuito secondo i termini presenti nel file [LICENSE](./LICENSE).
