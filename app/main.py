from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

users = [
    {"id": 1, "name": "Alice", "role": "admin", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "role": "viewer", "email": "bob@example.com"},
    {"id": 3, "name": "Carol", "role": "editor", "email": "carol@example.com"},
]

VALID_USERNAME = "alice"
VALID_PASSWORD = "password123"
ACCESS_TOKEN = "fake-token-alice"


def _is_authorized(authorization: str | None) -> bool:
    return authorization == f"Bearer {ACCESS_TOKEN}"


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def ui_home() -> FileResponse:
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="frontend not found")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/login")
def login(payload: dict) -> dict[str, str]:
    username = payload.get("username")
    password = payload.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username and password are required",
        )

    if username != VALID_USERNAME or password != VALID_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
        )

    return {"token": ACCESS_TOKEN}


@app.get("/users")
def list_users(authorization: str | None = Header(default=None)) -> list[dict]:
    if not _is_authorized(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )
    return users


@app.get("/users/{user_id}")
def get_user(user_id: int, authorization: str | None = Header(default=None)) -> dict:
    if not _is_authorized(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )

    for user in users:
        if user["id"] == user_id:
            return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: dict, authorization: str | None = Header(default=None)) -> dict:
    if not _is_authorized(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )

    name = payload.get("name")
    role = payload.get("role")
    email = payload.get("email")

    if not name or not role or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="name, role, and email are required",
        )

    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid email",
        )

    next_id = max(user["id"] for user in users) + 1 if users else 1
    new_user = {"id": next_id, "name": name, "role": role, "email": email}
    users.append(new_user)
    return new_user


@app.put("/users/{user_id}")
def update_user(user_id: int, payload: dict, authorization: str | None = Header(default=None)) -> dict:
    if not _is_authorized(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )

    name = payload.get("name")
    role = payload.get("role")
    email = payload.get("email")

    if not name or not role or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="name, role, and email are required",
        )

    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid email",
        )

    for user in users:
        if user["id"] == user_id:
            user["name"] = name
            user["role"] = role
            user["email"] = email
            return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, authorization: str | None = Header(default=None)) -> None:
    if not _is_authorized(authorization):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )

    for index, user in enumerate(users):
        if user["id"] == user_id:
            users.pop(index)
            return

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
