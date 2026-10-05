from conftest import TestingSessionLocal

from app.models import User, UserRole


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
            "title": "Errore accesso al mio account",
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
    assert classification.json()["suggested_category"] == "Account"

    suggestion = client.post(f"/api/ai/tickets/{ticket['id']}/suggest-reply", headers=bearer(agent_token))
    assert suggestion.status_code == 200
    assert suggestion.json()["source"] == "fallback"
    assert "preso in carico" in suggestion.json()["reply"]

    denied = client.post(f"/api/ai/tickets/{ticket['id']}/classify", headers=bearer(customer_token))
    assert denied.status_code == 403
