def register_payload() -> dict[str, str]:
    return {
        "name": "Cliente Demo",
        "email": "cliente@example.com",
        "password": "PasswordDemo2026!",
    }


def test_customer_can_register_login_and_read_their_profile(client) -> None:
    registration = client.post("/api/auth/register", json=register_payload())

    assert registration.status_code == 201
    registered = registration.json()
    assert registered["token_type"] == "bearer"
    assert registered["user"]["email"] == "cliente@example.com"
    assert registered["user"]["role"] == "customer"

    login = client.post(
        "/api/auth/login",
        json={"email": "cliente@example.com", "password": "PasswordDemo2026!"},
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    profile = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["name"] == "Cliente Demo"


def test_registration_rejects_a_duplicate_email(client) -> None:
    assert client.post("/api/auth/register", json=register_payload()).status_code == 201

    duplicate = client.post("/api/auth/register", json=register_payload())
    assert duplicate.status_code == 409


def test_profile_requires_a_valid_token(client) -> None:
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_login_does_not_disclose_whether_an_account_exists(client) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "PasswordDemo2026!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Email o password non validi."
