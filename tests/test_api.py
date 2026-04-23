import pytest


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_success(client):
    response = client.post(
        "/login",
        json={"username": "alice", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json() == {"token": "fake-token-alice"}


def test_login_failure(client):
    response = client.post(
        "/login",
        json={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "invalid credentials"}


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "alice"},
        {"password": "password123"},
        {},
    ],
)
def test_login_missing_fields_returns_400(client, payload):
    response = client.post("/login", json=payload)

    assert response.status_code == 400
    assert response.json() == {"detail": "username and password are required"}


def test_get_user(client, auth_headers):
    response = client.get("/users/1", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Alice",
        "role": "admin",
        "email": "alice@example.com",
    }


def test_unauthorized_access(client):
    response = client.get("/users/1")

    assert response.status_code == 401
    assert response.json() == {"detail": "unauthorized"}


def test_get_user_not_found_returns_404(client, auth_headers):
    response = client.get("/users/9999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "user not found"}


def test_create_user(client, auth_headers):
    payload = {"name": "Dave", "role": "viewer", "email": "dave@example.com"}
    response = client.post("/users", json=payload, headers=auth_headers)

    assert response.status_code == 201
    created_user = response.json()
    assert "id" in created_user
    assert created_user["name"] == "Dave"
    assert created_user["role"] == "viewer"
    assert created_user["email"] == "dave@example.com"


def test_create_user_unauthorized_returns_401(client):
    payload = {"name": "Eve", "role": "viewer", "email": "eve@example.com"}
    response = client.post("/users", json=payload)

    assert response.status_code == 401
    assert response.json() == {"detail": "unauthorized"}


@pytest.mark.parametrize(
    "payload,expected_detail",
    [
        ({"name": "Eve", "role": "viewer"}, "name, role, and email are required"),
        ({"name": "Eve", "role": "viewer", "email": "not-an-email"}, "invalid email"),
    ],
)
def test_validation_errors(client, auth_headers, payload, expected_detail):
    response = client.post("/users", json=payload, headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {"detail": expected_detail}


@pytest.mark.parametrize(
    "user_id",
    [
        1,
        2,
        3,
    ],
)
def test_parameterized_user_lookup(client, auth_headers, user_id):
    response = client.get(f"/users/{user_id}", headers=auth_headers)

    assert response.status_code == 200
    user_data = response.json()
    assert user_data["id"] == user_id
    assert {"id", "name", "role", "email"}.issubset(user_data.keys())
