# Database TicketHub

PostgreSQL viene avviato dal servizio `postgres` definito in `../docker-compose.yml`.

Le migrazioni Alembic e il seed applicativo sono gestiti dal backend:

- migrazione iniziale: `../backend/alembic/versions/20261005_0001_initial_schema.py`;
- seed idempotente: `../backend/app/db/seed.py`;
- avvio automatico tramite `../backend/scripts/start.sh`.

In locale, con le dipendenze backend installate, i comandi equivalenti sono:

```bash
cd backend
alembic upgrade head
python -m app.db.seed
```

Il seed crea gli account demo `admin@tickethub.com`, `operatore@tickethub.com` e `cliente@tickethub.com`, oltre a categorie, ticket e messaggi. Le credenziali sono documentate nel README.
