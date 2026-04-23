"""
Test pyramid for `order_service` (unit, component, inter-service, contract).
"""

import pytest
import requests

import order_service.app.main as order_main
from order_service.app.main import _is_authorized, _is_valid_order_data


# -------------------------
# Unit tests (isolated logic)
# -------------------------
def test_is_valid_order_data_unit_valid_payload():
    payload = {"user_id": 1, "item": "Keyboard"}

    assert _is_valid_order_data(payload) is True


@pytest.mark.parametrize(
    "payload",
    [
        {"item": "Keyboard"},  # missing user_id
        {"user_id": 1},  # missing item
        {"user_id": 1, "item": ""},  # blank item
        {"user_id": 1, "item": "   "},  # whitespace-only item
        {"user_id": "1", "item": "Keyboard"},  # non-int user_id
    ],
)
def test_is_valid_order_data_unit_invalid_payloads(payload):
    assert _is_valid_order_data(payload) is False


def test_is_authorized_unit_valid_and_invalid_token():
    assert _is_authorized("Bearer fake-token-alice") is True
    assert _is_authorized("Bearer wrong-token") is False
    assert _is_authorized(None) is False


# --------------------------------------
# Component tests (intra-service, local)
# --------------------------------------
def test_health_check_component(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_order_success_component(client, auth_headers, monkeypatch):
    # Keep this test intra-service by stubbing the outbound user-service check.
    monkeypatch.setattr(order_main, "_user_exists_in_user_service", lambda user_id, authorization: "ok")
    order_main.orders.clear()

    payload = {"user_id": 1, "item": "Keyboard"}
    response = client.post("/orders", json=payload, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["user_id"] == 1
    assert response.json()["item"] == "Keyboard"
    assert "id" in response.json()


def test_create_order_missing_auth_component(client):
    payload = {"user_id": 1, "item": "Keyboard"}
    response = client.post("/orders", json=payload)

    assert response.status_code == 401
    assert response.json() == {"detail": "unauthorized"}


def test_create_order_invalid_body_component(client, auth_headers):
    payload = {"user_id": 1, "item": "   "}
    response = client.post("/orders", json=payload, headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {"error": "invalid order data"}


# ------------------------------------------------
# Component tests (inter-service via mocked HTTP)
# ------------------------------------------------
def test_create_order_user_not_found_interservice(client, auth_headers, monkeypatch):
    # Mock the outbound HTTP call to user service to simulate 404 user not found.
    monkeypatch.setattr(order_main, "_user_exists_in_user_service", lambda user_id, authorization: "not_found")

    payload = {"user_id": 999, "item": "Keyboard"}
    response = client.post("/orders", json=payload, headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {"error": "invalid user"}


def test_create_order_user_service_unauthorized_interservice(client, auth_headers, monkeypatch):
    monkeypatch.setattr(order_main, "_user_exists_in_user_service", lambda user_id, authorization: "unauthorized")

    payload = {"user_id": 1, "item": "Keyboard"}
    response = client.post("/orders", json=payload, headers=auth_headers)

    assert response.status_code == 401
    assert response.json() == {"detail": "unauthorized"}


def test_create_order_user_service_error_interservice(client, auth_headers, monkeypatch):
    monkeypatch.setattr(order_main, "_user_exists_in_user_service", lambda user_id, authorization: "error")

    payload = {"user_id": 1, "item": "Keyboard"}
    response = client.post("/orders", json=payload, headers=auth_headers)

    assert response.status_code == 400
    assert response.json() == {"error": "invalid user"}


def test_create_order_with_mocked_user_service_call_interservice(
    client, auth_headers, monkeypatch
):
    # Mock user service response to 200 and validate create order flow.
    # This validates inter-service behavior without running user_service.
    monkeypatch_called_with = {}

    def fake_user_exists(user_id, authorization):
        monkeypatch_called_with["user_id"] = user_id
        monkeypatch_called_with["authorization"] = authorization
        return "ok"

    order_main.orders.clear()
    monkeypatch.setattr(order_main, "_user_exists_in_user_service", fake_user_exists)

    payload = {"user_id": 2, "item": "Monitor"}
    response = client.post("/orders", json=payload, headers=auth_headers)

    assert response.status_code == 201
    assert response.json()["user_id"] == 2
    assert response.json()["item"] == "Monitor"
    assert monkeypatch_called_with == {
        "user_id": 2,
        "authorization": "Bearer fake-token-alice",
    }


# --------------------------------------------
# Contract tests (user service response shape)
# --------------------------------------------
@pytest.mark.contract
def test_user_response_contract():
    # Real contract test against user service response shape.
    # This catches breaking payload changes across services.
    try:
        login_response = requests.post(
            "http://127.0.0.1:8000/login",
            json={"username": "alice", "password": "password123"},
            timeout=5,
        )
    except requests.RequestException:
        pytest.skip("User service is not running on http://127.0.0.1:8000")

    if login_response.status_code != 200:
        pytest.skip("Expected user service is unavailable on port 8000 (login endpoint not returning 200)")

    token = login_response.json().get("token")
    assert token == "fake-token-alice"

    response = requests.get(
        "http://127.0.0.1:8000/users/1",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )

    assert response.status_code == 200
    user_data = response.json()

    assert {"id", "name", "role", "email"}.issubset(user_data.keys())
    assert isinstance(user_data["id"], int)
    assert isinstance(user_data["name"], str)
    assert isinstance(user_data["role"], str)
    assert isinstance(user_data["email"], str)
