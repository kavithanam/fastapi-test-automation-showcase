import atexit
import os
import subprocess
import sys
import time
from typing import List

import pytest
import requests


USER_SERVICE_URL = "http://127.0.0.1:8000"
ORDER_SERVICE_URL = "http://127.0.0.1:8001"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PYTEST_STARTED_PROCS: List[subprocess.Popen] = []


def _health_ok() -> bool:
    try:
        user_health = requests.get(f"{USER_SERVICE_URL}/health", timeout=2)
        order_health = requests.get(f"{ORDER_SERVICE_URL}/health", timeout=2)
    except requests.RequestException:
        return False
    return user_health.status_code == 200 and order_health.status_code == 200


def _start_local_services() -> None:
    if _health_ok():
        return

    if os.getenv("START_LOCAL_SERVICES", "0") != "1":
        return

    env = os.environ.copy()

    _PYTEST_STARTED_PROCS.append(
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
            cwd=REPO_ROOT,
            env=env,
        )
    )
    _PYTEST_STARTED_PROCS.append(
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "order_service.app.main:app", "--port", "8001"],
            cwd=REPO_ROOT,
            env=env,
        )
    )

    deadline = time.time() + 30
    while time.time() < deadline:
        if _health_ok():
            return
        time.sleep(0.25)

    raise RuntimeError("Failed to start local services for integration tests (8000/8001).")


def _stop_local_services() -> None:
    for proc in _PYTEST_STARTED_PROCS:
        if proc.poll() is None:
            proc.terminate()
    for proc in _PYTEST_STARTED_PROCS:
        if proc.poll() is None:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    _PYTEST_STARTED_PROCS.clear()


atexit.register(_stop_local_services)


@pytest.fixture(scope="session", autouse=True)
def ensure_integration_services_for_session():
    # Runs once per test session, before any integration tests in this package.
    if not _health_ok():
        _start_local_services()
    if not _health_ok():
        pytest.skip("Integration tests require user service (8000) and order service (8001) to be running")


@pytest.fixture(autouse=True)
def require_running_services():
    # Fast guard per test (in case a service died mid-run).
    if not _health_ok():
        pytest.skip("Integration tests require healthy services on ports 8000 and 8001")
