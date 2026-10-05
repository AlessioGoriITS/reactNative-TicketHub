# TicketHub — Piano dettagliato del progetto

## 1. Visione del progetto

TicketHub è una piattaforma web per la gestione professionale delle richieste di assistenza clienti. Gli utenti possono aprire ticket, seguirne lo stato e comunicare con il team di supporto; gli operatori possono classificare, assegnare e risolvere le richieste attraverso una dashboard centralizzata.

L’obiettivo è realizzare un prodotto semplice da usare ma credibile in un contesto aziendale, con autenticazione, ruoli, API REST, database relazionale, interfaccia web, Docker Compose e una funzionalità AI integrata nel backend.

## 2. Obiettivi della consegna

Il progetto dovrà:

- funzionare dopo un `git clone` e l’avvio tramite Docker Compose;
- essere organizzato come monorepo;
- comprendere frontend web, backend, API e database;
- permettere di creare, modificare, assegnare e chiudere ticket;
- distinguere almeno clienti, operatori e amministratori;
- integrare una funzionalità AI realmente utile;
- includere documentazione sufficiente per un altro sviluppatore;
- fornire dati demo o una procedura di inizializzazione;
- essere presentabile con una demo completa e ripetibile.

## 3. Utenti e ruoli

### Cliente

- crea nuovi ticket;
- visualizza i propri ticket;
- aggiunge messaggi e allegati;
- riapre un ticket risolto entro un periodo definito;
- valuta l’assistenza ricevuta.

### Operatore

- visualizza i ticket assegnati o disponibili;
- modifica stato, priorità e categoria;
- assegna ticket agli operatori;
- risponde al cliente;
- usa l’assistente AI per classificazione e risposta suggerita;
- consulta statistiche operative.

### Amministratore

- gestisce utenti, ruoli e categorie;
- visualizza tutti i ticket;
- configura SLA e priorità;
- consulta audit log e statistiche globali.

## 4. Funzionalità principali

### Autenticazione e autorizzazione

- registrazione e login;
- autenticazione tramite JWT;
- password salvate con hashing sicuro;
- endpoint protetti in base al ruolo;
- logout lato client;
- recupero password come funzionalità opzionale.

### Gestione ticket

Ogni ticket deve avere almeno:

- titolo;
- descrizione;
- categoria;
- priorità: bassa, media, alta, urgente;
- stato: aperto, in lavorazione, in attesa del cliente, risolto, chiuso;
- autore;
- operatore assegnato;
- date di creazione, aggiornamento e chiusura;
- eventuale scadenza SLA.

Operazioni richieste:

- creazione;
- visualizzazione dettaglio;
- modifica dei dati autorizzati;
- assegnazione;
- cambio stato;
- ricerca e filtri;
- ordinamento e paginazione;
- chiusura e riapertura;
- esportazione CSV come funzionalità opzionale.

### Conversazione del ticket

Ogni ticket deve contenere una conversazione cronologica composta da messaggi. I messaggi devono indicare autore, testo, data e ruolo dell’autore. È utile distinguere tra messaggi visibili al cliente e note interne visibili solo agli operatori.

### Dashboard

La dashboard operatore deve mostrare:

- ticket aperti;
- ticket urgenti;
- ticket assegnati all’operatore corrente;
- ticket in ritardo rispetto allo SLA;
- tempo medio di risoluzione;
- distribuzione per categoria e stato.

### Notifiche

Versione minima: notifiche visualizzate nell’applicazione. Versione estesa: email quando un ticket viene creato, assegnato, aggiornato o risolto.

## 5. Funzionalità AI

La funzionalità AI principale sarà un assistente per gli operatori.

### Classificazione automatica

Quando viene creato un ticket, il backend può inviare titolo e descrizione al modello AI. Il modello restituisce:

- categoria suggerita;
- priorità suggerita;
- breve riassunto;
- parole chiave;
- eventuale indicazione di urgenza.

L’operatore deve poter accettare o modificare i suggerimenti: l’AI non deve cambiare automaticamente dati importanti senza conferma.

### Risposta suggerita

Nel dettaglio del ticket, l’operatore può richiedere una bozza di risposta. Il backend invia all’AI la descrizione e la conversazione recente e riceve una risposta professionale da modificare prima dell’invio.

### Provider configurabili

Il backend dovrà supportare almeno una modalità:

- OpenAI o OpenRouter tramite chiave API;
- modalità locale con Ollama, come alternativa opzionale.

La scelta del provider sarà gestita tramite variabili d’ambiente. Se il servizio AI non è disponibile, il ticket deve comunque poter essere creato e gestito normalmente.

## 6. Architettura proposta

```text
TicketHub/
├── frontend/              # Applicazione web React
├── backend/               # API REST e logica applicativa
├── database/              # Migrazioni e seed iniziale
├── docs/                  # Documentazione tecnica e screenshot
├── docker-compose.yml
├── .env.example
├── README.md
└── PIANO_PROGETTO_TICKETHUB.md
```

### Stack consigliato

- Frontend: React, TypeScript e Vite;
- UI: Tailwind CSS o libreria di componenti;
- Backend: FastAPI e Python;
- ORM: SQLAlchemy;
- Database: PostgreSQL;
- Migrazioni: Alembic;
- Autenticazione: JWT;
- AI: OpenAI/OpenRouter oppure Ollama;
- Container: Docker e Docker Compose;
- Test backend: Pytest;
- Test frontend: Vitest e React Testing Library.

## 7. Modello dati

### users

- `id`;
- `name`;
- `email` univoca;
- `password_hash`;
- `role`;
- `is_active`;
- `created_at`.

### categories

- `id`;
- `name`;
- `description`;
- `is_active`.

### tickets

- `id`;
- `ticket_number` leggibile, ad esempio `TK-000001`;
- `title`;
- `description`;
- `status`;
- `priority`;
- `category_id`;
- `customer_id`;
- `assigned_to_id`;
- `ai_summary`;
- `ai_suggested_priority`;
- `created_at`;
- `updated_at`;
- `resolved_at`.

### ticket_messages

- `id`;
- `ticket_id`;
- `author_id`;
- `body`;
- `is_internal`;
- `created_at`.

### attachments

- `id`;
- `ticket_id`;
- `message_id`;
- `file_name`;
- `file_path` o URL;
- `mime_type`;
- `file_size`;
- `created_at`.

### audit_logs

- `id`;
- `user_id`;
- `ticket_id` opzionale;
- `action`;
- `old_value`;
- `new_value`;
- `created_at`.

## 8. API REST

### Autenticazione

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Ticket

- `GET /api/tickets`
- `POST /api/tickets`
- `GET /api/tickets/{id}`
- `PATCH /api/tickets/{id}`
- `DELETE /api/tickets/{id}` solo per amministratori, se necessario;
- `POST /api/tickets/{id}/assign`
- `POST /api/tickets/{id}/resolve`
- `POST /api/tickets/{id}/reopen`

### Messaggi

- `GET /api/tickets/{id}/messages`
- `POST /api/tickets/{id}/messages`

### AI

- `POST /api/ai/tickets/{id}/classify`
- `POST /api/ai/tickets/{id}/suggest-reply`

### Dashboard e amministrazione

- `GET /api/dashboard/summary`
- `GET /api/dashboard/metrics`
- `GET /api/categories`
- `POST /api/categories` amministratore;
- `GET /api/users` amministratore.

Ogni endpoint dovrà restituire errori coerenti, codici HTTP corretti e messaggi leggibili. La documentazione Swagger/OpenAPI dovrà essere disponibile in ambiente di sviluppo.

## 9. Pagine frontend

- Login;
- registrazione;
- dashboard;
- lista ticket;
- dettaglio ticket e conversazione;
- creazione ticket;
- profilo utente;
- gestione utenti, categorie e impostazioni per amministratori;
- pagina errore e stato di caricamento.

La UI deve essere responsive, avere stati di caricamento e messaggi d’errore chiari. I filtri della lista ticket devono essere sincronizzabili con i parametri URL.

## 10. Docker Compose

Il file `docker-compose.yml` dovrà avviare almeno:

- `frontend`;
- `backend`;
- `postgres`.

Opzionali:

- `ollama` per AI locale;
- `mailhog` per simulare le email;
- `adminer` per ispezionare il database in sviluppo.

Requisiti:

- healthcheck del database;
- volume persistente PostgreSQL;
- file `.env.example` completo;
- comando di migrazione e seed documentato;
- porte non conflittuali e configurabili.

## 11. Dati demo

Il seed iniziale dovrebbe creare:

- un amministratore;
- due operatori;
- due clienti;
- almeno quattro categorie;
- ticket in stati e priorità differenti;
- messaggi di esempio.

Le credenziali demo devono essere indicate chiaramente nel README e non devono essere utilizzate in produzione.

## 12. Piano di sviluppo

### Fase 1 — Setup

- inizializzare il monorepo;
- creare i progetti frontend e backend;
- configurare Docker Compose;
- avviare PostgreSQL;
- aggiungere `.env.example`;
- configurare linting e formattazione.

### Fase 2 — Database e autenticazione

- definire modelli e relazioni;
- creare migrazioni;
- aggiungere seed;
- implementare registrazione e login;
- aggiungere middleware JWT e controllo ruoli.

### Fase 3 — API ticket

- CRUD ticket;
- filtri e paginazione;
- assegnazione;
- cambio stato;
- messaggi e note interne;
- audit log.

### Fase 4 — Frontend operativo

- layout e navigazione;
- pagine autenticazione;
- dashboard;
- lista e dettaglio ticket;
- form di creazione;
- conversazione e risposta;
- gestione ruoli.

### Fase 5 — Integrazione AI

- creare il client AI nel backend;
- definire prompt strutturati;
- validare la risposta del modello;
- implementare classificazione;
- implementare risposta suggerita;
- aggiungere fallback e gestione errori;
- mostrare sempre all’operatore che il testo è generato dall’AI.

### Fase 6 — Qualità e documentazione

- test backend;
- test dei componenti principali frontend;
- verifica permessi;
- test con Docker da ambiente pulito;
- screenshot;
- README definitivo;
- revisione UX e gestione errori.

## 13. Criteri di accettazione

Il progetto sarà considerato completato quando:

- `docker compose up --build` avvia i servizi;
- il database viene inizializzato senza operazioni manuali non documentate;
- un cliente può registrarsi e creare un ticket;
- un operatore può visualizzare, assegnare e risolvere il ticket;
- cliente e operatore vedono solo le informazioni consentite dal proprio ruolo;
- i messaggi del ticket sono persistenti;
- la dashboard mostra dati reali dal database;
- l’AI classifica un ticket o genera una risposta suggerita;
- il sistema continua a funzionare anche se il provider AI è irraggiungibile;
- il README consente a un collega di installare e provare il progetto;
- non sono presenti chiavi API reali nel repository.

## 14. README finale

Il README dovrà contenere:

- titolo e descrizione;
- screenshot o GIF della demo;
- architettura;
- tecnologie usate;
- prerequisiti;
- configurazione `.env`;
- avvio con Docker Compose;
- credenziali demo;
- comandi per migrazioni e seed;
- URL frontend, API e Swagger;
- descrizione dell’integrazione AI;
- comandi per test e lint;
- struttura del repository;
- limitazioni note;
- funzionalità future;
- riferimenti tecnici e API di terze parti.

## 15. Funzionalità future

- notifiche email reali;
- allegati su storage S3-compatible;
- ricerca full-text e semantica;
- knowledge base con suggerimenti AI;
- SLA configurabili per categoria;
- integrazione Slack o Microsoft Teams;
- webhook per sistemi esterni;
- analisi della soddisfazione dei clienti;
- supporto multilingua;
- deploy su un servizio cloud.

## 16. Rischi e decisioni progettuali

- L’AI deve essere un supporto all’operatore, non un decisore automatico.
- Le chiavi API devono essere caricate esclusivamente tramite variabili d’ambiente.
- I messaggi interni non devono essere restituiti alle API del cliente.
- Gli allegati devono avere limiti di dimensione e tipo MIME consentito.
- Il progetto deve funzionare anche senza AI, usando un messaggio di fallback.
- Per mantenere il progetto gestibile, la prima versione non deve includere chat realtime, microservizi separati o deployment cloud obbligatorio.

## 17. Demo consigliata

1. Accedere come cliente demo.
2. Creare un ticket relativo a un problema tecnico.
3. Mostrare la classificazione AI proposta.
4. Accedere come operatore.
5. Visualizzare il nuovo ticket nella dashboard.
6. Accettare o modificare categoria e priorità.
7. Generare una risposta suggerita dall’AI.
8. Inviare la risposta e risolvere il ticket.
9. Tornare al cliente e mostrare lo storico aggiornato.

Questa demo copre autenticazione, ruoli, persistenza, API, frontend, workflow e integrazione AI in pochi minuti.
