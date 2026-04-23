"""
Cross-service integration and end-to-end tests (real HTTP) across user and order services.

These tests use real HTTP calls and require both services to be running:
- user service on http://127.0.0.1:8000
- order service on http://127.0.0.1:8001
"""

import requests
import pytest


USER_SERVICE_URL = "http://127.0.0.1:8000"
ORDER_SERVICE_URL = "http://127.0.0.1:8001"


# --------------------------------------
# Integration tests (real local services)
# --------------------------------------
@pytest.mark.integration
def test_integration_login_and_get_token():
    response = requests.post(
        f"{USER_SERVICE_URL}/login",
        json={"username": "alice", "password": "password123"},
        timeout=5,
    )

    assert response.status_code == 200
    assert "token" in response.json()
    assert response.json()["token"] == "fake-token-alice"


@pytest.mark.integration
def test_integration_create_order_with_real_services():
    login_response = requests.post(
        f"{USER_SERVICE_URL}/login",
        json={"username": "alice", "password": "password123"},
        timeout=5,
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    order_response = requests.post(
        f"{ORDER_SERVICE_URL}/orders",
        json={"user_id": 1, "item": "Keyboard"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )

    assert order_response.status_code == 201
    created_order = order_response.json()
    assert "id" in created_order
    assert created_order["user_id"] == 1
    assert created_order["item"] == "Keyboard"


@pytest.mark.integration
def test_integration_negative_invalid_auth():
    response = requests.post(
        f"{ORDER_SERVICE_URL}/orders",
        json={"user_id": 1, "item": "Keyboard"},
        headers={"Authorization": "Bearer invalid-token"},
        timeout=5,
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "unauthorized"}


@pytest.mark.integration
def test_integration_negative_invalid_user():
    login_response = requests.post(
        f"{USER_SERVICE_URL}/login",
        json={"username": "alice", "password": "password123"},
        timeout=5,
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    order_response = requests.post(
        f"{ORDER_SERVICE_URL}/orders",
        json={"user_id": 9999, "item": "Keyboard"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )

    assert order_response.status_code == 400
    assert order_response.json() == {"error": "invalid user"}


# ------------------------------
# End-to-end test flow examples
# ------------------------------
@pytest.mark.e2e
def test_e2e_login_then_create_order():
    # End-to-end flow:
    # 1) Login against user service
    login_response = requests.post(
        f"{USER_SERVICE_URL}/login",
        json={"username": "alice", "password": "password123"},
        timeout=5,
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # 2) Use token to create order in order service
    order_response = requests.post(
        f"{ORDER_SERVICE_URL}/orders",
        json={"user_id": 1, "item": "Mouse"},
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    assert order_response.status_code == 201

    # 3) Verify response fields: id, user_id, item
    created_order = order_response.json()
    assert "id" in created_order
    assert created_order["user_id"] == 1
    assert created_order["item"] == "Mouse"
