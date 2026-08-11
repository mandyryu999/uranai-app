import hashlib
import hmac
import os
import secrets
import time

from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import select

from admin_ui import ADMIN_HTML
from database import SessionLocal
from models import BirthProfile, SanmeigakuChart
from sanmeigaku_engine import calculate_chart
from server import app, mcp, sanmeigaku_chart_to_dict


PROTECTED_PREFIXES = ("/admin", "/api/", "/docs", "/openapi.json")
SESSION_COOKIE = "uranai_admin_session"
SESSION_MAX_AGE = 60 * 60 * 12

LOGIN_HTML = r'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>uranai-app 管理者ログイン</title>
  <style>
    :root{font-family:Inter,"Noto Sans JP",system-ui,sans-serif;color:#1f2937;background:#f5f3ef}
    *{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:linear-gradient(145deg,#f7f2e8,#efe7d9)}
    .login{width:min(420px,100%);background:#fff;border:1px solid #ddd4c5;border-radius:18px;padding:28px;box-shadow:0 14px 40px #00000012}
    h1{font-size:24px;margin:0 0 6px;color:#211b15}.sub{color:#766d62;font-size:13px;margin-bottom:24px}
    label{display:block;font-size:12px;color:#62594f;margin:14px 0 6px}input{width:100%;border:1px solid #d7cfc2;border-radius:10px;padding:12px;font:inherit}
    button{width:100%;margin-top:20px;border:0;border-radius:10px;padding:12px 14px;background:#8b6b2f;color:#fff;font:inherit;font-weight:700;cursor:pointer}
    .error{background:#fff1f1;color:#9b2c2c;border:1px solid #efcaca;border-radius:9px;padding:10px 12px;font-size:13px;margin-bottom:14px}
    .note{margin-top:18px;color:#8a8176;font-size:11px;line-height:1.6;text-align:center}
  </style>
</head>
<body>
  <form class="login" method="post" action="/login">
    <h1>uranai-app</h1>
    <div class="sub">鑑定士 管理者ログイン</div>
    __ERROR__
    <label for="username">管理者ID</label>
    <input id="username" name="username" autocomplete="username" required autofocus>
    <label for="password">パスワード</label>
    <input id="password" name="password" type="password" autocomplete="current-password" required>
    <button type="submit">ログイン</button>
    <div class="note">相談者情報を保護するため、管理者のみ利用できます。</div>
  </form>
</body>
</html>'''


def _auth_config() -> tuple[str, str]:
    return os.environ.get("ADMIN_USERNAME", ""), os.environ.get("ADMIN_PASSWORD", "")


def _session_secret() -> str:
    configured = os.environ.get("ADMIN_SESSION_SECRET", "")
    if configured:
        return configured
    username, password = _auth_config()
    return hashlib.sha256(f"uranai-app:{username}:{password}".encode()).hexdigest()


def _mcp_token() -> str:
    return os.environ.get("MCP_AUTH_TOKEN", "")


def _is_protected(path: str) -> bool:
    return path == "/admin" or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES[1:])


def _make_session(username: str) -> str:
    expires = int(time.time()) + SESSION_MAX_AGE
    payload = f"{username}|{expires}"
    signature = hmac.new(_session_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}|{signature}"


def _valid_session(value: str | None) -> bool:
    if not value:
        return False
    try:
        username, expires_text, signature = value.split("|", 2)
        expires = int(expires_text)
    except (ValueError, TypeError):
        return False
    if expires < int(time.time()):
        return False
    expected_username, _ = _auth_config()
    if not expected_username or not secrets.compare_digest(username, expected_username):
        return False
    payload = f"{username}|{expires}"
    expected = hmac.new(_session_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    return secrets.compare_digest(signature, expected)


def _mcp_unauthorized(message: str = "MCP token required") -> Response:
    return JSONResponse(status_code=401, content={"detail": message}, headers={"WWW-Authenticate": "Bearer"})


@app.middleware("http")
async def protect_routes(request: Request, call_next):
    path = request.url.path

    if path == "/":
        return RedirectResponse(url="/admin", status_code=307)

    if path in ("/login", "/logout", "/health"):
        return await call_next(request)

    if path.startswith("/mcp"):
        expected_token = _mcp_token()
        if not expected_token:
            return JSONResponse(status_code=503, content={"detail": "MCP authentication is not configured"})
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return _mcp_unauthorized()
        if not secrets.compare_digest(authorization[7:], expected_token):
            return _mcp_unauthorized("Invalid MCP token")
        return await call_next(request)

    if not _is_protected(path):
        return await call_next(request)

    expected_username, expected_password = _auth_config()
    if not expected_username or not expected_password:
        return RedirectResponse(url="/login?config=missing", status_code=303)

    if not _valid_session(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse(url="/login", status_code=303)

    return await call_next(request)


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    if _valid_session(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse(url="/admin", status_code=303)
    config_missing = request.query_params.get("config") == "missing"
    error = '<div class="error">管理者ID・パスワードがサーバーにまだ設定されていません。</div>' if config_missing else ""
    return LOGIN_HTML.replace("__ERROR__", error)


@app.post("/login", include_in_schema=False)
def login(username: str = Form(...), password: str = Form(...)):
    expected_username, expected_password = _auth_config()
    if not expected_username or not expected_password:
        return HTMLResponse(LOGIN_HTML.replace("__ERROR__", '<div class="error">管理者設定が未完了です。</div>'), status_code=503)
    if not (secrets.compare_digest(username, expected_username) and secrets.compare_digest(password, expected_password)):
        return HTMLResponse(LOGIN_HTML.replace("__ERROR__", '<div class="error">管理者IDまたはパスワードが違います。</div>'), status_code=401)
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        _make_session(username),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response


@app.get("/logout", include_in_schema=False)
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


def _calculate_and_save(client_id: int) -> dict:
    with SessionLocal() as db:
        profile = db.scalar(select(BirthProfile).where(BirthProfile.client_id == client_id))
        if profile is None:
            raise ValueError("birth profile not found")
        known_birth_time = None if profile.birth_time_unknown else profile.birth_time
        result = calculate_chart(profile.birth_date, known_birth_time)
        detail = result.pop("calculation_detail")
        chart = db.scalar(select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id))
        if chart is None:
            chart = SanmeigakuChart(client_id=client_id, **result)
            db.add(chart)
        else:
            for field, value in result.items():
                setattr(chart, field, value)
        db.commit()
        db.refresh(chart)
        return {"chart": sanmeigaku_chart_to_dict(chart), "detail": detail}


@mcp.tool()
def auto_calculate_sanmeigaku(client_id: int) -> dict:
    return _calculate_and_save(client_id)


def _admin_html_with_auto_calculation() -> str:
    old = '<button class="secondary small" onclick="openChartModal()">登録・編集</button>'
    new = '<span><button class="gold small" onclick="autoCalculateChart()">自動計算</button> <button class="secondary small" onclick="openChartModal()">登録・編集</button></span>'
    header_old = '<div class="header-actions"><button class="gold" onclick="openClientModal(true)">＋ 新規相談者</button><a href="/docs" style="color:#ddd;text-decoration:none">API Docs</a></div>'
    header_new = '<div class="header-actions"><button class="gold" onclick="openClientModal(true)">＋ 新規相談者</button><a href="/docs" style="color:#ddd;text-decoration:none">API Docs</a><a href="/logout" style="color:#ddd;text-decoration:none">ログアウト</a></div>'
    script = r'''
async function autoCalculateChart(){
  if(!selectedId)return;
  if(!currentContext?.birth_profile?.birth_date){alert('先に出生情報で生年月日を登録してください');return;}
  if(!confirm('生年月日から命式を自動計算し、現在の命式を更新します。よろしいですか？'))return;
  try{
    const d=await api(`/api/clients/${selectedId}/sanmeigaku-chart/auto-calculate`,{method:'POST'});
    await selectClient(selectedId);
    const warning=d.detail?.boundary_warning?`\n\n注意: ${d.detail.boundary_warning}`:'';
    alert(`命式を自動計算しました。\n${d.chart.year_pillar} / ${d.chart.month_pillar} / ${d.chart.day_pillar}\n${d.chart.tenchusatsu}${warning}`);
  }catch(e){alert(e.message)}
}
'''
    return ADMIN_HTML.replace(old, new).replace(header_old, header_new).replace("</script>", script + "</script>")


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard():
    return _admin_html_with_auto_calculation()


@app.post("/api/clients/{client_id}/sanmeigaku-chart/auto-calculate")
def auto_calculate_sanmeigaku_chart(client_id: int):
    try:
        return _calculate_and_save(client_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"chart calculation failed: {exc}") from exc
