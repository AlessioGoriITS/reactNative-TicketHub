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


def promote_to_admin(user_id: int) -> None:
    with TestingSessionLocal() as database:
        user = database.get(User, user_id)
        assert user is not None
        user.role = UserRole.ADMIN
        database.commit()


def test_dashboard_metrics_are_scoped_to_the_authenticated_customer(client) -> None:
    first_token, _ = register(client, "first-dashboard@example.com", "Primo Cliente")
    second_token, _ = register(client, "second-dashboard@example.com", "Secondo Cliente")
    response = client.post(
        "/api/tickets",
        headers=bearer(first_token),
        json={
            "description": "Il cliente desidera verificare una richiesta di supporto privata.",
        },
    )
    assert response.status_code == 201

    first_summary = client.get("/api/dashboard/summary", headers=bearer(first_token))
    second_summary = client.get("/api/dashboard/summary", headers=bearer(second_token))
    assert first_summary.status_code == 200
    assert first_summary.json()["total_tickets"] == 1
    assert second_summary.json()["total_tickets"] == 0


def test_admin_can_manage_categories_and_user_roles(client) -> None:
    admin_token, admin_id = register(client, "admin@example.com", "Admin Demo")
    _, target_id = register(client, "target@example.com", "Target User")
    promote_to_admin(admin_id)

    forbidden = client.get("/api/admin/users", headers=bearer(client.post(
        "/api/auth/login", json={"email": "target@example.com", "password": "PasswordDemo2026!"}
    ).json()["access_token"]))
    assert forbidden.status_code == 403

    users = client.get("/api/admin/users", headers=bearer(admin_token))
    assert users.status_code == 200
    assert len(users.json()) == 2

    updated_user = client.patch(
        f"/api/admin/users/{target_id}", headers=bearer(admin_token), json={"role": "agent"}
    )
    assert updated_user.status_code == 200
    assert updated_user.json()["role"] == "agent"

    category = client.post(
        "/api/categories",
        headers=bearer(admin_token),
        json={"name": "Integrazioni", "description": "Richieste su servizi collegati."},
    )
    assert category.status_code == 201
    assert category.json()["name"] == "Integrazioni"

    deactivated = client.patch(
        f"/api/categories/{category.json()['id']}",
        headers=bearer(admin_token),
        json={"is_active": False},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False
