# Multi-Service Test Automation Demo (FastAPI + Pytest + Selenium)

A small, credible portfolio project demonstrating a practical **test pyramid** on a simple multi-service FastAPI backend, plus a minimal browser UI and Selenium UI tests.

**Suggested public repository name:** `fastapi-test-automation-showcase` (rename the GitHub repository to any professional name you prefer; it does not need to match your local folder name).

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

## Run tests

```bash
pytest -v
```

## Run user service (existing)

From the project root:

```bash
uvicorn app.main:app --reload --port 8000
```

## Run order service (new)

From the project root:

```bash
uvicorn order_service.app.main:app --reload --port 8001
```

## Run order service tests

```bash
pytest -v order_service/tests
```

## Run integration tests (cross-service)

Both services must be running locally before these tests are executed.

```bash
pytest -v integration_tests
```

## Run the web UI (served by the user service)

The UI is static files + JS served from the same FastAPI app (no separate UI port by default).

```bash
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/`.

## Run UI tests (Selenium + pytest)

Prerequisites:
- Google Chrome installed (Selenium will manage `chromedriver` via `webdriver-manager` on first run; internet access may be required once)
- User service running on `http://127.0.0.1:8000` (or set `UI_BASE_URL`)

```bash
pytest -v -m ui ui_tests
```

Optional: headless mode

```bash
UI_HEADLESS=1 pytest -v -m ui ui_tests
```

## Run the full test suite (API + UI + cross-service) in one command

To run *everything* without manually starting the two services in separate terminals, opt in to test-time startup of local `uvicorn` processes:

```bash
START_LOCAL_SERVICES=1 pytest -v
```

Notes:
- `START_LOCAL_SERVICES=1` will try to start `app.main:app` on `8000` and `order_service.app.main:app` on `8001` (and stop them at the end of the pytest session).
- If you already have something bound to `8000` or `8001`, free those ports or run services manually and omit `START_LOCAL_SERVICES=1`.
