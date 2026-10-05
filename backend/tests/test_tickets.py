from conftest import TestingSessionLocal

from app.models import User, UserRole


def register_and_token(client, email: str, name: str = "Cliente Ticket") -> tuple[str, int]:
    response = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": "PasswordDemo2026!"},
    )
    assert response.status_code == 201
    body = response.json()
    return body["access_token"], body["user"]["id"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_customer_can_create_list_and_discuss_a_ticket(client) -> None:
    token, _ = register_and_token(client, "customer@example.com")

    created = client.post(
        "/api/tickets",
        headers=headers(token),
        json={
            "title": "Errore durante il login",
            "description": "Dopo l'accesso la pagina visualizza un errore imprevisto.",
            "priority": "high",
        },
    )
    assert created.status_code == 201
    ticket = created.json()
    assert ticket["ticket_number"] == "TK-000001"
    assert ticket["status"] == "open"

    ticket_list = client.get("/api/tickets?status=open", headers=headers(token))
    assert ticket_list.status_code == 200
    assert ticket_list.json()["total"] == 1

    message = client.post(
        f"/api/tickets/{ticket['id']}/messages",
        headers=headers(token),
        json={"body": "Ho provato anche a svuotare la cache del browser."},
    )
    assert message.status_code == 201

    detail = client.get(f"/api/tickets/{ticket['id']}", headers=headers(token))
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) == 1


def test_customers_cannot_read_tickets_created_by_other_customers(client) -> None:
    first_token, _ = register_and_token(client, "first@example.com", "Primo Cliente")
    ticket = client.post(
        "/api/tickets",
        headers=headers(first_token),
        json={
            "title": "Richiesta riservata",
            "description": "Questa richiesta non deve essere visibile agli altri clienti.",
        },
    ).json()
    second_token, _ = register_and_token(client, "second@example.com", "Secondo Cliente")

    forbidden_ticket = client.get(f"/api/tickets/{ticket['id']}", headers=headers(second_token))
    assert forbidden_ticket.status_code == 404

    internal_note = client.post(
        f"/api/tickets/{ticket['id']}/messages",
        headers=headers(first_token),
        json={"body": "Nota privata", "is_internal": True},
    )
    assert internal_note.status_code == 403

    priority_change = client.patch(
        f"/api/tickets/{ticket['id']}",
        headers=headers(first_token),
        json={"priority": "urgent"},
    )
    assert priority_change.status_code == 403


def test_operator_can_assign_resolve_and_add_internal_note(client) -> None:
    customer_token, _ = register_and_token(client, "owner@example.com", "Cliente Owner")
    ticket = client.post(
        "/api/tickets",
        headers=headers(customer_token),
        json={
            "title": "Impossibile scaricare la fattura",
            "description": "Il pulsante di download non produce alcun file PDF.",
        },
    ).json()
    agent_token, agent_id = register_and_token(client, "agent@example.com", "Operatore Demo")
    with TestingSessionLocal() as database:
        agent = database.get(User, agent_id)
        assert agent is not None
        agent.role = UserRole.AGENT
        database.commit()

    assigned = client.post(
        f"/api/tickets/{ticket['id']}/assign",
        headers=headers(agent_token),
        json={"assigned_to_id": agent_id},
    )
    assert assigned.status_code == 200
    assert assigned.json()["status"] == "in_progress"
    assert assigned.json()["assigned_to"]["id"] == agent_id

    internal_note = client.post(
        f"/api/tickets/{ticket['id']}/messages",
        headers=headers(agent_token),
        json={"body": "Verificare i permessi del servizio documentale.", "is_internal": True},
    )
    assert internal_note.status_code == 201

    resolved = client.post(f"/api/tickets/{ticket['id']}/resolve", headers=headers(agent_token))
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    customer_detail = client.get(f"/api/tickets/{ticket['id']}", headers=headers(customer_token))
    assert customer_detail.status_code == 200
    assert customer_detail.json()["messages"] == []

    reopened = client.post(f"/api/tickets/{ticket['id']}/reopen", headers=headers(customer_token))
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "open"
