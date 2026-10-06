# TicketHub

TicketHub è una piattaforma full-stack per la gestione professionale delle richieste di assistenza clienti. Clienti, operatori e amministratori lavorano sullo stesso flusso: apertura, classificazione, conversazione, assegnazione, risoluzione e analisi delle richieste.

Il progetto è un monorepo avviabile in locale tramite Docker Compose. Include database PostgreSQL, API REST documentata, frontend web, autenticazione JWT, ruoli, dati demo, test e Ollama locale per generare automaticamente titolo, priorità e sintesi dei ticket.

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
- apertura di ticket per un prodotto demo, con la sola descrizione del problema;
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
- sintesi AI ricalcolabile e suggerimento di risposta, sempre modificabili prima dell’uso.

### Amministratori

- tutte le autorizzazioni degli operatori;
- gestione utenti, ruoli e stato di attivazione;
- creazione e disattivazione delle categorie;
- chiusura definitiva dei ticket.

### Intelligenza artificiale

L’AI è integrata nel backend, non nel browser. Alla creazione di un ticket il backend invia la descrizione a **Ollama locale** e riceve un JSON strutturato con:

- titolo del ticket generato automaticamente;
- priorità `low`, `medium`, `high` o `urgent`;
- sintesi breve salvata nel ticket.
- categoria scelta tra quelle attive configurate dall’amministratore.

Il cliente non può inviare né modificare titolo, priorità o categoria: queste proprietà sono calcolate dal backend e salvate insieme al ticket. I nuovi titoli generati hanno un limite di 120 caratteri; i titoli esistenti non vengono riscritti durante la riclassificazione. Se il modello restituisce una categoria vuota o non valida, il backend prova una classificazione deterministica dalla descrizione, sempre limitata alle categorie attive. Se non viene individuata una corrispondenza ragionevole, la categoria resta non specificata. Un operatore può ricalcolare la sintesi e ottenere una bozza di risposta; quest’ultima non viene mai inviata automaticamente.

Docker Compose avvia Ollama e scarica automaticamente il modello `llama3.2:1b` al primo avvio. Se il servizio o il modello non fosse momentaneamente disponibile, il backend applica un fallback deterministico, registra la fonte nell’audit log e continua a creare il ticket senza bloccare il cliente.

## Architettura e tecnologie

```text
Browser
   │
   ▼
React + TypeScript + Vite ───────► FastAPI REST API ───────► PostgreSQL 16
                                         │
                                         └── Ollama locale (container Docker)
```

| Componente | Tecnologia | Responsabilità |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite, React Router | Interfaccia web responsive e gestione sessione JWT |
| Backend | Python, FastAPI, SQLAlchemy, Alembic | API REST, regole di business, ruoli, audit e AI |
| Database | PostgreSQL 16 | utenti, categorie, ticket, messaggi, allegati e audit log |
| Container | Docker Compose, Nginx | avvio coerente dei servizi e distribuzione del frontend |
| AI | Ollama + `llama3.2:1b` | titolo, priorità, sintesi e categoria automatica dei ticket |

Per i dettagli dei flussi e della struttura dei dati, consultare [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Avvio rapido con Docker

### Prerequisiti

- Git;
- Docker Desktop avviato, con Docker Compose v2;
- porte locali `5173`, `8000`, `5432` e `11434` disponibili;
- connessione Internet al primo avvio, per scaricare l’immagine e il modello locale (circa 1,3 GB).
- almeno 12 GB liberi nello spazio gestito da Docker Desktop: l’immagine ufficiale di Ollama include i runtime CPU/GPU e può occupare circa 9,4 GB, a cui si aggiunge il modello.

Non sono richiesti Node.js, Python, PostgreSQL, chiavi API né un’installazione manuale di Ollama: tutti i servizi, incluso il modello locale, sono gestiti da Docker Compose. Per un’esperienza fluida è consigliabile assegnare almeno 4 GB di RAM a Docker Desktop.

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

Al primo avvio `ollama-init` scarica `llama3.2:1b`; questa operazione può richiedere alcuni minuti e una connessione Internet. Il backend avvia subito l’applicazione e usa il fallback deterministico fino a quando il modello non è pronto; il job ritenta automaticamente se il registry di Ollama non fosse momentaneamente raggiungibile. Attendere che `backend`, `frontend`, `postgres` e `ollama` siano `healthy`, quindi aprire:

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

Sono disponibili anche i comandi `make up`, `make down`, `make logs` e `make build` nei sistemi che includono `make`.

## Account e dati demo

Il seed viene eseguito una sola volta sul database inizialmente vuoto.

| Ruolo | Email | Password |
| --- | --- | --- |
| Amministratore | `admin@tickethub.com` | `TicketHubDemo2026!` |
| Operatore | `operatore@tickethub.com` | `TicketHubDemo2026!` |
| Cliente | `cliente@tickethub.com` | `TicketHubDemo2026!` |

Vengono creati anche quattro categorie, due ticket e messaggi di esempio. Queste credenziali sono esclusivamente per la demo e non devono essere riutilizzate fuori dall’ambiente locale.

## Configurazione AI locale

Il file `.env.example` è già predisposto per Ollama in locale:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:1b
AI_TIMEOUT_SECONDS=120
```

Non cambiare `OLLAMA_BASE_URL` quando si usa Docker Compose: `ollama` è il nome del servizio interno. Il servizio `ollama-init` scarica il modello configurato nella variabile `OLLAMA_MODEL` e lo conserva nel volume Docker `ollama_data`, quindi i successivi avvii non lo riscaricano. Se la rete o il registry di Ollama non sono disponibili, il job continua a ritentare senza bloccare l’applicazione.

Per verificare manualmente il modello:

```bash
docker compose exec ollama ollama list
```

Il modello scelto è piccolo abbastanza per una demo su CPU e adatto ai tre compiti richiesti: titolo, priorità e sintesi in italiano. Non viene usata alcuna API cloud né inviata alcuna informazione a servizi esterni.

## API principali

La documentazione completa e testabile è disponibile in Swagger su `/docs`.

| Area | Endpoint principali |
| --- | --- |
| Sistema | `GET /health`, `GET /api/health` |
| Autenticazione | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| Ticket | `GET/POST /api/tickets`, `GET/PATCH /api/tickets/{id}` — il `POST` crea automaticamente titolo, priorità, sintesi e categoria con Ollama |
| Prodotti | `GET /api/products` — catalogo dei prodotti demo selezionabili all’apertura di un ticket |
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

La suite backend copre registrazione, login, token, ruoli, isolamento dei ticket, associazione a un prodotto demo, generazione automatica di titolo, priorità, sintesi e categoria, note interne, assegnazione, risoluzione, dashboard, amministrazione e fallback AI.

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

## Catalogo prodotti demo

Per rendere la demo più realistica, ogni nuovo ticket creato dalla web app è collegato a uno dei prodotti di esempio inizializzati dal seed:

- `TicketHub Desk`: portale web per l’assistenza clienti;
- `TicketHub Mobile`: app mobile per clienti e operatori;
- `TicketHub Insights`: dashboard e reportistica operativa;
- `TicketHub Connect API`: API per integrare TicketHub con servizi esterni.

I prodotti sono dati fittizi e servono esclusivamente a simulare un contesto di assistenza multi-prodotto. L’associazione resta facoltativa a livello API per compatibilità con ticket generici, ma è richiesta nella web app.

## Sicurezza e limiti

- Le password sono memorizzate con hash bcrypt; non vengono mai salvate in chiaro.
- Le API proteggono le operazioni tramite JWT e controlli di ruolo lato backend.
- Le note interne non vengono restituite agli account cliente.
- Messaggi pubblici e note interne aggiornano la data del ticket e il suo ordine nelle attività recenti.
- Le azioni importanti sono registrate in `audit_logs`.
- Il progetto non invia email reali e non carica ancora allegati fisici: la tabella è predisposta ma lo storage non è implementato.
- L’AI può produrre classificazioni imprecise: gli operatori devono verificare priorità e categoria assegnate automaticamente.
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
