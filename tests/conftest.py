from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app import main as user_main
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer fake-token-alice"}


@pytest.fixture(autouse=True)
def reset_users_state():
    # Keep tests independent by restoring in-memory users after each test.
    original_users = deepcopy(user_main.users)
    yield
    user_main.users[:] = original_users
