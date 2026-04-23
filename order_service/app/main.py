import requests
from fastapi import FastAPI, Header, status
from fastapi.responses import JSONResponse


app = FastAPI()

orders = []
USER_SERVICE_BASE_URL = "http://127.0.0.1:8000"
EXPECTED_TOKEN = "fake-token-alice"


def _is_authorized(authorization: str | None) -> bool:
    return authorization == f"Bearer {EXPECTED_TOKEN}"


def _is_valid_order_data(payload: dict) -> bool:
    user_id = payload.get("user_id")
    item = payload.get("item")
    return isinstance(user_id, int) and isinstance(item, str) and item.strip() != ""


def _user_exists_in_user_service(user_id: int, authorization: str) -> str:
    """
    Returns one of:
    - "ok": user exists and auth accepted by user service
    - "unauthorized": user service rejected auth
    - "not_found": user does not exist
    - "error": any network/other unexpected issue
    """
    try:
        response = requests.get(
            f"{USER_SERVICE_BASE_URL}/users/{user_id}",
            headers={"Authorization": authorization},
            timeout=5,
        )
    except requests.RequestException:
        return "error"

    if response.status_code == 200:
        return "ok"
    if response.status_code == 401:
        return "unauthorized"
    if response.status_code == 404:
        return "not_found"
    return "error"


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/orders")
def create_order(payload: dict, authorization: str | None = Header(default=None)):
    if not _is_authorized(authorization):
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "unauthorized"})

    if not _is_valid_order_data(payload):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid order data"},
        )

    user_check = _user_exists_in_user_service(payload["user_id"], authorization)

    if user_check == "unauthorized":
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "unauthorized"})
    if user_check == "not_found":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "invalid user"})
    if user_check != "ok":
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": "invalid user"})

    next_id = len(orders) + 1
    order = {"id": next_id, "user_id": payload["user_id"], "item": payload["item"]}
    orders.append(order)

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=order)
