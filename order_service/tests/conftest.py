import pytest
from fastapi.testclient import TestClient

from order_service.app import main as order_main
from order_service.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer fake-token-alice"}


@pytest.fixture(autouse=True)
def reset_orders_state():
    # Keep tests independent by clearing in-memory orders each test.
    order_main.orders.clear()
