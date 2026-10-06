from conftest import TestingSessionLocal
from datetime import datetime, timezone
import pytest

from app.models import Product, Ticket, User, UserRole


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
            "description": "Dopo l'accesso la pagina visualizza un errore imprevisto.",
        },
    )
    assert created.status_code == 201
    ticket = created.json()
    assert ticket["ticket_number"] == "TK-000001"
    assert ticket["status"] == "open"
    assert ticket["priority"] == "medium"
    assert ticket["title"]
    assert ticket["ai_summary"]

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


def test_customer_can_associate_a_ticket_with_a_demo_product(client) -> None:
    token, _ = register_and_token(client, "product-customer@example.com")
    with TestingSessionLocal() as database:
        product = Product(code="MOBILE", name="TicketHub Mobile", description="App mobile demo")
        database.add(product)
        database.commit()
        product_id = product.id

    products = client.get("/api/products", headers=headers(token))
    assert products.status_code == 200
    assert products.json()[0]["code"] == "MOBILE"

    created = client.post(
        "/api/tickets",
        headers=headers(token),
        json={
            "product_id": product_id,
            "description": "L'app mobile non mostra gli aggiornamenti del mio ticket.",
        },
    )

    assert created.status_code == 201
    assert created.json()["product"]["name"] == "TicketHub Mobile"


def test_customers_cannot_read_tickets_created_by_other_customers(client) -> None:
    first_token, _ = register_and_token(client, "first@example.com", "Primo Cliente")
    ticket = client.post(
        "/api/tickets",
        headers=headers(first_token),
        json={
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


def test_customer_cannot_set_ticket_title_or_priority_at_creation(client) -> None:
    token, _ = register_and_token(client, "automatic@example.com")

    response = client.post(
        "/api/tickets",
        headers=headers(token),
        json={
            "title": "Titolo scelto dal cliente",
            "description": "Il cliente prova a impostare manualmente i dati classificati dall'AI.",
            "priority": "urgent",
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize("internal", [False, True])
def test_message_updates_ticket_timestamp_order_and_note_visibility(client, internal):
    customer_token, _ = register_and_token(client, "message-owner@example.com")
    ticket_ids = []
    for _ in range(2):
        result = client.post("/api/tickets", headers=headers(customer_token), json={
            "description": "Il report mensile non viene esportato correttamente."
        })
        assert result.status_code == 201
        ticket_ids.append(result.json()["id"])
    agent_token, agent_id = register_and_token(client, "message-agent@example.com")
    with TestingSessionLocal() as database:
        database.get(User, agent_id).role = UserRole.AGENT
        database.get(Ticket, ticket_ids[0]).updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
        database.get(Ticket, ticket_ids[1]).updated_at = datetime(2021, 1, 1, tzinfo=timezone.utc)
        database.commit()
    before = client.get(f"/api/tickets/{ticket_ids[0]}", headers=headers(customer_token)).json()
    message = client.post(f"/api/tickets/{ticket_ids[0]}/messages", headers=headers(agent_token), json={
        "body": "Aggiornamento di verifica.", "is_internal": internal
    })
    assert message.status_code == 201
    detail = client.get(f"/api/tickets/{ticket_ids[0]}", headers=headers(customer_token)).json()
    assert detail["updated_at"] > before["updated_at"]
    assert len(detail["messages"]) == (0 if internal else 1)
    listing = client.get("/api/tickets", headers=headers(customer_token)).json()
    assert listing["items"][0]["id"] == ticket_ids[0]
