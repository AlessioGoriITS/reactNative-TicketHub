# Guida alla demo

Questa sequenza mostra le funzionalità principali in circa cinque minuti.

1. Avviare lo stack con `docker compose up --build` e aprire <http://localhost:5173>.
2. Accedere come cliente demo (`cliente@tickethub.local`).
3. Aprire un nuovo ticket, selezionando una categoria e una priorità.
4. Controllare la dashboard e il dettaglio del ticket appena creato.
5. Disconnettersi e accedere come operatore (`operatore@tickethub.local`).
6. Aprire il ticket, assegnarlo attraverso l’API Swagger oppure usando gli endpoint REST e aggiungere una nota interna.
7. Usare **Analizza con AI** e **Suggerisci risposta**: mostrare che il risultato è modificabile e che, senza provider configurato, l’interfaccia indica il fallback locale.
8. Inviare una risposta visibile al cliente e segnare il ticket come risolto.
9. Tornare all’account cliente: il ticket risulta aggiornato, ma la nota interna non è visibile.
10. Accedere come amministratore (`admin@tickethub.local`) e mostrare Swagger su <http://localhost:8000/docs> per la gestione utenti e categorie.

## Casi da evidenziare

- isolamento: un cliente non può leggere i ticket di un altro cliente;
- ruoli: un cliente non può creare note interne o cambiare la priorità;
- resilienza: l’assenza del provider AI non rende indisponibile il servizio;
- tracciabilità: cambi di stato, assegnazioni, messaggi e azioni AI generano eventi di audit.
