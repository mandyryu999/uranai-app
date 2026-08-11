import base64
import os
import secrets

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from admin_ui import ADMIN_HTML
from server import app


PROTECTED_PREFIXES = ("/admin", "/api/", "/docs", "/openapi.json")


def _auth_config() -> tuple[str, str]:
    return os.environ.get("ADMIN_USERNAME", ""), os.environ.get("ADMIN_PASSWORD", "")


def _is_protected(path: str) -> bool:
    return path == "/admin" or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES[1:])


def _unauthorized(message: str = "Authentication required") -> Response:
    return JSONResponse(
        status_code=401,
        content={"detail": message},
        headers={"WWW-Authenticate": 'Basic realm="uranai-app admin", charset="UTF-8"'},
    )


@app.middleware("http")
async def protect_admin_routes(request: Request, call_next):
    if not _is_protected(request.url.path):
        return await call_next(request)

    expected_username, expected_password = _auth_config()
    if not expected_username or not expected_password:
        return JSONResponse(
            status_code=503,
            content={"detail": "Admin authentication is not configured"},
        )

    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Basic "):
        return _unauthorized()

    try:
        decoded = base64.b64decode(authorization[6:], validate=True).decode("utf-8")
        username, password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return _unauthorized("Invalid authentication header")

    username_ok = secrets.compare_digest(username, expected_username)
    password_ok = secrets.compare_digest(password, expected_password)
    if not (username_ok and password_ok):
        return _unauthorized("Invalid username or password")

    return await call_next(request)


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard():
    return ADMIN_HTML
