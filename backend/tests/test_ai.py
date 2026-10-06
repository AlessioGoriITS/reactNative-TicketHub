from conftest import TestingSessionLocal
import pytest

from app.api.routes.tickets import get_active_category_names, get_automatic_category
from app.models import Category, User, UserRole
from app.services import ai as ai_service


def register(client, email: str, name: str) -> tuple[str, int]:
    response = client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": "PasswordDemo2026!"},
    )
    assert response.status_code == 201
    body = response.json()
    return body["access_token"], body["user"]["id"]


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_staff_receives_safe_ai_fallbacks_when_no_provider_is_configured(client) -> None:
    customer_token, _ = register(client, "ai-customer@example.com", "Cliente AI")
    ticket = client.post(
        "/api/tickets",
        headers=bearer(customer_token),
        json={
            "description": "Dopo il login il sistema mostra un errore e non riesco ad accedere.",
        },
    ).json()
    agent_token, agent_id = register(client, "ai-agent@example.com", "Operatore AI")
    with TestingSessionLocal() as database:
        agent = database.get(User, agent_id)
        assert agent is not None
        agent.role = UserRole.AGENT
        database.commit()

    classification = client.post(f"/api/ai/tickets/{ticket['id']}/classify", headers=bearer(agent_token))
    assert classification.status_code == 200
    assert classification.json()["source"] == "fallback"
    assert classification.json()["suggested_category"] is None

    suggestion = client.post(f"/api/ai/tickets/{ticket['id']}/suggest-reply", headers=bearer(agent_token))
    assert suggestion.status_code == 200
    assert suggestion.json()["source"] == "fallback"
    assert "preso in carico" in suggestion.json()["reply"]

    denied = client.post(f"/api/ai/tickets/{ticket['id']}/classify", headers=bearer(customer_token))
    assert denied.status_code == 403


def test_ticket_creation_persists_title_priority_and_summary_generated_by_ai(client, monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "_request_json",
        lambda _messages: {
            "title": "Accesso bloccato per tutti gli utenti",
            "summary": "Il portale non consente più l'accesso agli utenti del cliente.",
            "suggested_priority": "low",
            "suggested_category": "Problema tecnico",
            "keywords": ["accesso", "blocco"],
        },
    )
    customer_token, _ = register(client, "creation-ai@example.com", "Cliente Creazione AI")
    with TestingSessionLocal() as database:
        database.add(Category(name="Problema tecnico", description="Errori applicativi"))
        database.commit()
        assert get_active_category_names(database) == ["Problema tecnico"]
        assert get_automatic_category("Problema tecnico", database) is not None

    created = client.post(
        "/api/tickets",
        headers=bearer(customer_token),
        json={"description": "In produzione nessun dipendente riesce ad accedere al portale."},
    )

    assert created.status_code == 201
    ticket = created.json()
    assert ticket["title"] == "Accesso bloccato per tutti gli utenti"
    assert ticket["priority"] == "high"
    assert ticket["ai_suggested_priority"] == "high"
    assert ticket["ai_summary"] == "Il portale non consente più l'accesso agli utenti del cliente."
    assert ticket["category"]["name"] == "Problema tecnico"


@pytest.mark.parametrize("suggestion", [None, "", "Categoria inventata"])
def test_invalid_category_uses_active_fallback_on_creation_and_reclassification(client, monkeypatch, suggestion):
    monkeypatch.setattr(ai_service, "_request_json", lambda _: {
        "title": "Errore nell’esportazione PDF del report mensile",
        "summary": "Errore 500 durante l'esportazione del report.",
        "suggested_priority": "medium", "suggested_category": suggestion,
    })
    with TestingSessionLocal() as database:
        database.add(Category(name="Problema tecnico", is_active=True))
        database.commit()
    token, _ = register(client, "fallback-category@example.com", "Cliente")
    created = client.post("/api/tickets", headers=bearer(token), json={
        "description": "Errore 500 durante l'esportazione PDF del report mensile."
    })
    assert created.status_code == 201
    ticket = created.json()
    assert ticket["category"]["name"] == "Problema tecnico"
    agent_token, agent_id = register(client, "category-agent@example.com", "Operatore")
    with TestingSessionLocal() as database:
        database.get(User, agent_id).role = UserRole.AGENT
        database.commit()
    response = client.post(f"/api/ai/tickets/{ticket['id']}/classify", headers=bearer(agent_token))
    assert response.status_code == 200
    assert response.json()["suggested_category"] == "Problema tecnico"
    detail = client.get(f"/api/tickets/{ticket['id']}", headers=bearer(token)).json()
    assert detail["category"]["name"] == "Problema tecnico"
    assert detail["title"] == ticket["title"]


@pytest.mark.parametrize("active", [True, False])
def test_provider_unavailable_never_assigns_inactive_category(client, active):
    with TestingSessionLocal() as database:
        database.add(Category(name="Problema tecnico", is_active=active))
        database.commit()
    token, _ = register(client, "offline-category@example.com", "Cliente")
    response = client.post("/api/tickets", headers=bearer(token), json={
        "description": "Errore 500 durante l'esportazione PDF del report mensile."
    })
    assert response.status_code == 201
    category = response.json()["category"]
    assert (category["name"] if category else None) == ("Problema tecnico" if active else None)


def test_inactive_model_category_and_unknown_problem_are_unassigned(client, monkeypatch):
    monkeypatch.setattr(ai_service, "_request_json", lambda _: {
        "title": "Richiesta di informazioni sul servizio",
        "summary": "Richiesta generica.", "suggested_priority": "medium",
        "suggested_category": "Problema tecnico",
    })
    with TestingSessionLocal() as database:
        database.add(Category(name="Problema tecnico", is_active=False))
        database.commit()
    token, _ = register(client, "inactive-category@example.com", "Cliente")
    created = client.post("/api/tickets", headers=bearer(token), json={
        "description": "Vorrei maggiori dettagli sulle caratteristiche del servizio."
    })
    assert created.status_code == 201
    assert created.json()["category"] is None


def test_generated_and_fallback_titles_are_bounded_and_remove_test_preamble():
    description = "Test manuale di consegna: " + "Errore esportazione PDF del report mensile " * 8
    for title in (ai_service._normalise_title(description, description), ai_service._fallback_title(description)):
        assert 5 <= len(title) <= 120
        assert not title.lower().startswith("test manuale")
    assert ai_service._normalise_title(None, "...") == "Richiesta di assistenza"
