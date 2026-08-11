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


def _mcp_token() -> str:
    return os.environ.get("MCP_AUTH_TOKEN", "")


def _is_protected(path: str) -> bool:
    return path == "/admin" or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES[1:])


def _unauthorized(message: str = "Authentication required") -> Response:
    return JSONResponse(
        status_code=401,
        content={"detail": message},
        headers={"WWW-Authenticate": 'Basic realm="uranai-app admin", charset="UTF-8"'},
    )


def _mcp_unauthorized(message: str = "MCP token required") -> Response:
    return JSONResponse(
        status_code=401,
        content={"detail": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.middleware("http")
async def protect_routes(request: Request, call_next):
    path = request.url.path

    if path.startswith("/mcp"):
        expected_token = _mcp_token()
        if not expected_token:
            return JSONResponse(
                status_code=503,
                content={"detail": "MCP authentication is not configured"},
            )
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return _mcp_unauthorized()
        supplied_token = authorization[7:]
        if not secrets.compare_digest(supplied_token, expected_token):
            return _mcp_unauthorized("Invalid MCP token")
        return await call_next(request)

    if not _is_protected(path):
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
