"""Idempotent development data used by the local demo environment."""

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Category, Ticket, TicketMessage, TicketPriority, TicketStatus, User, UserRole


DEMO_PASSWORD_HASH = "$2b$12$WJ0Hlax7R4cUYqgqsF3H3ef0Ewt0P7VWSBgnF3Aje.nmIfp7LgH56"


def get_or_create_user(
    email: str, name: str, role: UserRole, database_user: User | None = None
) -> User:
    """Return an existing demo user or construct the user to persist."""

    if database_user is not None:
        return database_user
    return User(name=name, email=email, role=role, password_hash=DEMO_PASSWORD_HASH)


def seed() -> None:
    """Add demo accounts, categories and tickets if the database is empty."""

    with SessionLocal() as database:
        if database.scalar(select(User.id).limit(1)) is not None:
            return

        admin = get_or_create_user("admin@tickethub.local", "Amministratore Demo", UserRole.ADMIN)
        agent = get_or_create_user("operatore@tickethub.local", "Giulia Bianchi", UserRole.AGENT)
        customer = get_or_create_user("cliente@tickethub.local", "Marco Rossi", UserRole.CUSTOMER)
        database.add_all([admin, agent, customer])

        technical = Category(name="Problema tecnico", description="Accesso, errori e malfunzionamenti.")
        billing = Category(name="Fatturazione", description="Pagamenti, fatture e rinnovi.")
        account = Category(name="Account", description="Profilo, credenziali e autorizzazioni.")
        general = Category(name="Informazioni generali", description="Richieste commerciali e informative.")
        database.add_all([technical, billing, account, general])
        database.flush()

        first_ticket = Ticket(
            ticket_number="TK-000001",
            title="Impossibile accedere al portale clienti",
            description="Dopo il login il portale continua a reindirizzarmi alla pagina iniziale.",
            status=TicketStatus.IN_PROGRESS,
            priority=TicketPriority.HIGH,
            category=technical,
            customer=customer,
            assigned_to=agent,
            ai_summary="Il cliente segnala un ciclo di reindirizzamento dopo l'autenticazione.",
            ai_suggested_priority=TicketPriority.HIGH,
        )
        second_ticket = Ticket(
            ticket_number="TK-000002",
            title="Richiesta copia fattura settembre",
            description="Vorrei ricevere una copia della fattura relativa al mese di settembre.",
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            category=billing,
            customer=customer,
            ai_summary="Richiesta amministrativa per la duplicazione di una fattura.",
            ai_suggested_priority=TicketPriority.LOW,
        )
        database.add_all([first_ticket, second_ticket])
        database.flush()

        database.add_all(
            [
                TicketMessage(
                    ticket=first_ticket,
                    author=customer,
                    body="Il problema si presenta sia da Chrome sia da Firefox.",
                ),
                TicketMessage(
                    ticket=first_ticket,
                    author=agent,
                    body="Stiamo verificando la configurazione della sessione. Ti aggiorneremo a breve.",
                ),
                TicketMessage(
                    ticket=second_ticket,
                    author=customer,
                    body="La fattura è intestata a Rossi Consulting S.r.l.",
                ),
            ]
        )
        database.commit()


if __name__ == "__main__":
    seed()
