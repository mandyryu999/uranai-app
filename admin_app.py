import base64
import os
import secrets

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy import select

from admin_ui import ADMIN_HTML
from database import SessionLocal
from models import BirthProfile, SanmeigakuChart
from sanmeigaku_engine import calculate_chart
from server import app, sanmeigaku_chart_to_dict


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

    if not _is_protected(path):
        return await call_next(request)

    expected_username, expected_password = _auth_config()
    if not expected_username or not expected_password:
        return JSONResponse(status_code=503, content={"detail": "Admin authentication is not configured"})

    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Basic "):
        return _unauthorized()
    try:
        decoded = base64.b64decode(authorization[6:], validate=True).decode("utf-8")
        username, password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return _unauthorized("Invalid authentication header")
    if not (secrets.compare_digest(username, expected_username) and secrets.compare_digest(password, expected_password)):
        return _unauthorized("Invalid username or password")
    return await call_next(request)


def _admin_html_with_auto_calculation() -> str:
    old = '<button class="secondary small" onclick="openChartModal()">登録・編集</button>'
    new = '<span><button class="gold small" onclick="autoCalculateChart()">自動計算</button> <button class="secondary small" onclick="openChartModal()">登録・編集</button></span>'
    script = r'''
async function autoCalculateChart(){
  if(!selectedId)return;
  if(!currentContext?.birth_profile?.birth_date){alert('先に出生情報で生年月日を登録してください');return;}
  if(!confirm('生年月日から命式を自動計算し、現在の命式を更新します。よろしいですか？'))return;
  try{
    const d=await api(`/api/clients/${selectedId}/sanmeigaku-chart/auto-calculate`,{method:'POST'});
    await selectClient(selectedId);
    alert(`命式を自動計算しました。\n${d.chart.year_pillar} / ${d.chart.month_pillar} / ${d.chart.day_pillar}\n${d.chart.tenchusatsu}`);
  }catch(e){alert(e.message)}
}
'''
    html = ADMIN_HTML.replace(old, new)
    return html.replace("</script>", script + "</script>")


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard():
    return _admin_html_with_auto_calculation()


@app.post("/api/clients/{client_id}/sanmeigaku-chart/auto-calculate")
def auto_calculate_sanmeigaku_chart(client_id: int):
    """保存済み生年月日から命式を自動計算し、算命学命式へ保存します。"""
    with SessionLocal() as db:
        profile = db.scalar(select(BirthProfile).where(BirthProfile.client_id == client_id))
        if profile is None:
            raise HTTPException(status_code=404, detail="birth profile not found")
        try:
            result = calculate_chart(profile.birth_date)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"chart calculation failed: {exc}") from exc

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
