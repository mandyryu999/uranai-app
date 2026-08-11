import hashlib
import hmac
import os
import secrets
import time

from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from admin_ui import ADMIN_HTML
from database import SessionLocal
from models import AdminUser, BirthProfile, SanmeigakuChart
from sanmeigaku_engine import calculate_chart
from secure_settings import (
    OPENAI_API_KEY_SETTING,
    delete_secret,
    get_openai_api_key_status,
    set_secret,
)
from server import app, mcp, sanmeigaku_chart_to_dict


PROTECTED_PREFIXES = ("/admin", "/api/", "/docs", "/openapi.json", "/settings/")
SESSION_COOKIE = "uranai_admin_session"
SESSION_MAX_AGE = 60 * 60 * 12
PASSWORD_ITERATIONS = 600_000

AUTH_CSS = r'''
:root{font-family:Inter,"Noto Sans JP",system-ui,sans-serif;color:#1f2937;background:#f5f3ef}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:linear-gradient(145deg,#f7f2e8,#efe7d9)}
.auth{width:min(440px,100%);background:#fff;border:1px solid #ddd4c5;border-radius:18px;padding:28px;box-shadow:0 14px 40px #00000012}
h1{font-size:24px;margin:0 0 6px;color:#211b15}.sub{color:#766d62;font-size:13px;margin-bottom:24px;line-height:1.6}
label{display:block;font-size:12px;color:#62594f;margin:14px 0 6px}input{width:100%;border:1px solid #d7cfc2;border-radius:10px;padding:12px;font:inherit}
button{width:100%;margin-top:20px;border:0;border-radius:10px;padding:12px 14px;background:#8b6b2f;color:#fff;font:inherit;font-weight:700;cursor:pointer}
.error{background:#fff1f1;color:#9b2c2c;border:1px solid #efcaca;border-radius:9px;padding:10px 12px;font-size:13px;margin-bottom:14px;line-height:1.5}
.success{background:#effbf2;color:#276738;border:1px solid #cdebd5;border-radius:9px;padding:10px 12px;font-size:13px;margin-bottom:14px;line-height:1.5}
.note{margin-top:18px;color:#8a8176;font-size:11px;line-height:1.6;text-align:center}
'''

LOGIN_HTML = r'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>uranai-app 管理者ログイン</title><style>__CSS__</style></head>
<body><form class="auth" method="post" action="/login">
<h1>uranai-app</h1><div class="sub">鑑定士 管理者ログイン</div>__ERROR__
<label for="username">管理者ID</label><input id="username" name="username" autocomplete="username" required autofocus>
<label for="password">パスワード</label><input id="password" name="password" type="password" autocomplete="current-password" required>
<button type="submit">ログイン</button><div class="note">相談者情報を保護するため、管理者のみ利用できます。</div>
</form></body></html>'''.replace("__CSS__", AUTH_CSS)

SETUP_HTML = r'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>uranai-app 初期管理者作成</title><style>__CSS__</style></head>
<body><form class="auth" method="post" action="/setup">
<h1>初期管理者を作成</h1><div class="sub">この画面は管理者がまだ1人も登録されていない時だけ表示されます。ここで決めたIDとパスワードが、今後の管理画面ログイン情報になります。</div>__ERROR__
<label for="username">管理者ID</label><input id="username" name="username" minlength="3" maxlength="120" autocomplete="username" required autofocus>
<label for="password">パスワード（12文字以上）</label><input id="password" name="password" type="password" minlength="12" maxlength="128" autocomplete="new-password" required>
<label for="password_confirm">パスワード確認</label><input id="password_confirm" name="password_confirm" type="password" minlength="12" maxlength="128" autocomplete="new-password" required>
<button type="submit">最初の管理者を作成</button><div class="note">パスワードは暗号学的ハッシュに変換して保存し、元の文字列はDBへ保存しません。</div>
</form></body></html>'''.replace("__CSS__", AUTH_CSS)

OPENAI_SETTINGS_HTML = r'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OpenAI API設定</title>
<style>
:root{font-family:Inter,"Noto Sans JP",system-ui,sans-serif;color:#1f2937;background:#f5f3ef}*{box-sizing:border-box}
body{margin:0;background:#f5f3ef}.top{background:#211b15;color:#fff;padding:16px 22px;display:flex;justify-content:space-between;align-items:center}.top a{color:#eee;text-decoration:none;margin-left:16px}
main{max-width:760px;margin:36px auto;padding:0 18px}.card{background:#fff;border:1px solid #ddd4c5;border-radius:16px;padding:24px;box-shadow:0 10px 30px #0000000b}
h1{margin:0 0 8px;font-size:25px}.sub{color:#766d62;font-size:13px;line-height:1.7;margin-bottom:22px}.status{padding:12px;border-radius:10px;margin:15px 0;background:#f5f3ef;font-size:13px;line-height:1.7}.ok{background:#effbf2;color:#276738}.warn{background:#fff7e8;color:#765313}
label{display:block;font-size:12px;color:#62594f;margin:15px 0 6px}input{width:100%;border:1px solid #d7cfc2;border-radius:10px;padding:12px;font:inherit}
button{border:0;border-radius:10px;padding:11px 16px;background:#8b6b2f;color:#fff;font:inherit;font-weight:700;cursor:pointer;margin-top:14px}.danger{background:#9b2c2c}.row{display:flex;gap:10px;flex-wrap:wrap}.note{font-size:12px;color:#7d7469;line-height:1.7;margin-top:15px}.msg{background:#effbf2;color:#276738;border-radius:9px;padding:10px 12px;margin-bottom:16px;font-size:13px}
</style></head><body>
<div class="top"><strong>uranai-app 設定</strong><div><a href="/admin">管理画面へ戻る</a><a href="/logout">ログアウト</a></div></div>
<main><div class="card"><h1>OpenAI API設定</h1><div class="sub">AI鑑定補助で使用するOpenAI APIキーを、このアプリから登録できます。保存後にAPIキー全体を画面へ再表示することはありません。</div>
__MESSAGE____STATUS__
<form method="post" action="/settings/openai"><label for="api_key">OpenAI APIキー</label><input id="api_key" name="api_key" type="password" autocomplete="off" placeholder="sk-..." required><button type="submit">APIキーを保存・更新</button></form>
<form method="post" action="/settings/openai/delete" onsubmit="return confirm('アプリに保存したOpenAI APIキーを削除しますか？')"><button class="danger" type="submit">アプリ保存のAPIキーを削除</button></form>
<div class="note">APIキーはPostgreSQLへ平文保存せず、サーバー内の専用暗号鍵で暗号化して保存します。専用暗号鍵はDockerの永続ボリュームに置かれます。</div>
</div></main></body></html>'''


def _render(template: str, error: str = "") -> str:
    block = f'<div class="error">{error}</div>' if error else ""
    return template.replace("__ERROR__", block)


def _admin_exists() -> bool:
    with SessionLocal() as db:
        return db.scalar(select(AdminUser.id).limit(1)) is not None


def _get_admin(username: str) -> AdminUser | None:
    with SessionLocal() as db:
        return db.scalar(select(AdminUser).where(AdminUser.username == username))


def _hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt_hex = salt_hex or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PASSWORD_ITERATIONS
    ).hex()
    return salt_hex, digest


def _verify_password(password: str, admin: AdminUser) -> bool:
    _, candidate = _hash_password(password, admin.password_salt)
    return secrets.compare_digest(candidate, admin.password_hash)


def _session_secret() -> str:
    configured = os.environ.get("ADMIN_SESSION_SECRET", "")
    if configured:
        return configured
    with SessionLocal() as db:
        admin = db.scalar(select(AdminUser).order_by(AdminUser.id).limit(1))
        seed = admin.password_hash if admin else "not-configured"
    return hashlib.sha256(f"uranai-app-session:{seed}".encode()).hexdigest()


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
    if expires < int(time.time()) or _get_admin(username) is None:
        return False
    payload = f"{username}|{expires}"
    expected = hmac.new(_session_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    return secrets.compare_digest(signature, expected)


def _mcp_unauthorized(message: str = "MCP token required") -> Response:
    return JSONResponse(status_code=401, content={"detail": message}, headers={"WWW-Authenticate": "Bearer"})


@app.middleware("http")
async def protect_routes(request: Request, call_next):
    path = request.url.path

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

    has_admin = _admin_exists()
    if path == "/":
        return RedirectResponse(url="/admin" if has_admin else "/setup", status_code=307)
    if path in ("/setup", "/login", "/logout", "/health"):
        return await call_next(request)
    if not _is_protected(path):
        return await call_next(request)
    if not has_admin:
        return RedirectResponse(url="/setup", status_code=303)
    if not _valid_session(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse(url="/login", status_code=303)
    return await call_next(request)


@app.get("/setup", response_class=HTMLResponse, include_in_schema=False)
def setup_page():
    if _admin_exists():
        return RedirectResponse(url="/login", status_code=303)
    return _render(SETUP_HTML)


@app.post("/setup", include_in_schema=False)
def create_initial_admin(username: str = Form(...), password: str = Form(...), password_confirm: str = Form(...)):
    if _admin_exists():
        return RedirectResponse(url="/login", status_code=303)
    username = username.strip()
    if len(username) < 3:
        return HTMLResponse(_render(SETUP_HTML, "管理者IDは3文字以上にしてください。"), status_code=400)
    if len(password) < 12:
        return HTMLResponse(_render(SETUP_HTML, "パスワードは12文字以上にしてください。"), status_code=400)
    if password != password_confirm:
        return HTMLResponse(_render(SETUP_HTML, "確認用パスワードが一致しません。"), status_code=400)
    salt, password_hash = _hash_password(password)
    try:
        with SessionLocal() as db:
            if db.scalar(select(AdminUser.id).limit(1)) is not None:
                return RedirectResponse(url="/login", status_code=303)
            db.add(AdminUser(username=username, password_salt=salt, password_hash=password_hash))
            db.commit()
    except IntegrityError:
        return HTMLResponse(_render(SETUP_HTML, "その管理者IDは使用できません。"), status_code=409)
    return RedirectResponse(url="/login?created=1", status_code=303)


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    if not _admin_exists():
        return RedirectResponse(url="/setup", status_code=303)
    if _valid_session(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse(url="/admin", status_code=303)
    message = '<div class="success">初期管理者を作成しました。登録したIDとパスワードでログインしてください。</div>' if request.query_params.get("created") == "1" else ""
    return LOGIN_HTML.replace("__ERROR__", message)


@app.post("/login", include_in_schema=False)
def login(username: str = Form(...), password: str = Form(...)):
    if not _admin_exists():
        return RedirectResponse(url="/setup", status_code=303)
    username = username.strip()
    admin = _get_admin(username)
    if admin is None or not _verify_password(password, admin):
        return HTMLResponse(_render(LOGIN_HTML, "管理者IDまたはパスワードが違います。"), status_code=401)
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(SESSION_COOKIE, _make_session(username), max_age=SESSION_MAX_AGE, httponly=True, secure=True, samesite="lax", path="/")
    return response


@app.get("/logout", include_in_schema=False)
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


def _openai_settings_page(message: str = "") -> str:
    status = get_openai_api_key_status()
    if status["configured"]:
        source_text = "アプリ内に暗号化保存" if status["source"] == "app" else "サーバー環境変数"
        status_html = f'<div class="status ok"><strong>設定済み</strong><br>保存元: {source_text}<br>キー: {status["masked"]}</div>'
    else:
        status_html = '<div class="status warn"><strong>未設定</strong><br>AI鑑定を実行するにはAPIキーを登録してください。</div>'
    message_html = f'<div class="msg">{message}</div>' if message else ""
    return OPENAI_SETTINGS_HTML.replace("__STATUS__", status_html).replace("__MESSAGE__", message_html)


@app.get("/settings/openai", response_class=HTMLResponse, include_in_schema=False)
def openai_settings(request: Request):
    message = "APIキーを保存しました。" if request.query_params.get("saved") == "1" else ""
    if request.query_params.get("deleted") == "1":
        message = "アプリ保存のAPIキーを削除しました。"
    return _openai_settings_page(message)


@app.post("/settings/openai", include_in_schema=False)
def save_openai_settings(api_key: str = Form(...)):
    api_key = api_key.strip()
    if len(api_key) < 20:
        return HTMLResponse(_openai_settings_page("APIキーの形式を確認してください。"), status_code=400)
    set_secret(OPENAI_API_KEY_SETTING, api_key)
    return RedirectResponse(url="/settings/openai?saved=1", status_code=303)


@app.post("/settings/openai/delete", include_in_schema=False)
def delete_openai_settings():
    delete_secret(OPENAI_API_KEY_SETTING)
    return RedirectResponse(url="/settings/openai?deleted=1", status_code=303)


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
    header_new = '<div class="header-actions"><button class="gold" onclick="openClientModal(true)">＋ 新規相談者</button><a href="/settings/openai" style="color:#ddd;text-decoration:none">AI設定</a><a href="/docs" style="color:#ddd;text-decoration:none">API Docs</a><a href="/logout" style="color:#ddd;text-decoration:none">ログアウト</a></div>'
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
