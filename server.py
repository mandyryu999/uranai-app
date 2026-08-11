from datetime import date, datetime, time, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from mcp.server.fastmcp import FastMCP
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from ai_service import build_reading_prompt, generate_reading
from database import Base, SessionLocal, engine
from models import BirthProfile, Client, Reading, SanmeigakuChart
from schemas import (
    AIReadingRequest,
    BirthProfileCreate,
    BirthProfileRead,
    BirthProfileUpdate,
    ClientCreate,
    ClientRead,
    ClientUpdate,
    ReadingCreate,
    ReadingRead,
    ReadingUpdate,
    SanmeigakuChartCreate,
    SanmeigakuChartRead,
    SanmeigakuChartUpdate,
)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def client_to_dict(client: Client) -> dict:
    return ClientRead.model_validate(client).model_dump(mode="json")


def birth_profile_to_dict(profile: BirthProfile) -> dict:
    return BirthProfileRead.model_validate(profile).model_dump(mode="json")


def sanmeigaku_chart_to_dict(chart: SanmeigakuChart) -> dict:
    return SanmeigakuChartRead.model_validate(chart).model_dump(mode="json")


def reading_to_dict(reading: Reading) -> dict:
    return ReadingRead.model_validate(reading).model_dump(mode="json")


def build_client_context(db: Session, client_id: int, reading_limit: int = 10) -> dict:
    """AI鑑定用に相談者情報を1つのJSONへまとめます。"""
    client = db.get(Client, client_id)
    if client is None:
        raise ValueError("client not found")

    reading_limit = max(1, min(reading_limit, 100))
    birth_profile = db.scalar(select(BirthProfile).where(BirthProfile.client_id == client_id))
    chart = db.scalar(select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id))
    readings = db.scalars(
        select(Reading)
        .where(Reading.client_id == client_id)
        .order_by(Reading.reading_at.desc(), Reading.id.desc())
        .limit(reading_limit)
    ).all()

    return {
        "client": client_to_dict(client),
        "birth_profile": birth_profile_to_dict(birth_profile) if birth_profile else None,
        "sanmeigaku_chart": sanmeigaku_chart_to_dict(chart) if chart else None,
        "readings": [reading_to_dict(reading) for reading in readings],
        "reading_count_included": len(readings),
    }


mcp = FastMCP("uranai-app")


@mcp.tool()
def db_now() -> str:
    with engine.connect() as conn:
        return str(conn.execute(text("SELECT now()")).scalar())


@mcp.tool()
def create_client(name: str, name_kana: str | None = None, phone: str | None = None, email: str | None = None, line_name: str | None = None, notes: str | None = None) -> dict:
    payload = ClientCreate(name=name, name_kana=name_kana, phone=phone, email=email, line_name=line_name, notes=notes)
    with SessionLocal() as db:
        client = Client(**payload.model_dump()); db.add(client); db.commit(); db.refresh(client)
        return client_to_dict(client)


@mcp.tool()
def search_clients(query: str = "", limit: int = 20) -> list[dict]:
    limit = max(1, min(limit, 100))
    with SessionLocal() as db:
        stmt = select(Client).order_by(Client.updated_at.desc()).limit(limit)
        if query.strip():
            pattern = f"%{query.strip()}%"
            stmt = select(Client).where(or_(Client.name.ilike(pattern), Client.name_kana.ilike(pattern), Client.phone.ilike(pattern), Client.email.ilike(pattern), Client.line_name.ilike(pattern))).order_by(Client.updated_at.desc()).limit(limit)
        return [client_to_dict(client) for client in db.scalars(stmt).all()]


@mcp.tool()
def set_birth_profile(client_id: int, birth_date: str, birth_time: str | None = None, birth_time_unknown: bool = False, birthplace_prefecture: str | None = None, birthplace_city: str | None = None, birthplace_detail: str | None = None, timezone: str = "Asia/Tokyo") -> dict:
    parsed_date = date.fromisoformat(birth_date)
    parsed_time = None if birth_time_unknown or not birth_time else time.fromisoformat(birth_time)
    payload = BirthProfileCreate(birth_date=parsed_date, birth_time=parsed_time, birth_time_unknown=birth_time_unknown, birthplace_prefecture=birthplace_prefecture, birthplace_city=birthplace_city, birthplace_detail=birthplace_detail, timezone=timezone)
    with SessionLocal() as db:
        if db.get(Client, client_id) is None: raise ValueError("client not found")
        profile = db.scalar(select(BirthProfile).where(BirthProfile.client_id == client_id))
        if profile is None:
            profile = BirthProfile(client_id=client_id, **payload.model_dump()); db.add(profile)
        else:
            for field, value in payload.model_dump().items(): setattr(profile, field, value)
        db.commit(); db.refresh(profile); return birth_profile_to_dict(profile)


@mcp.tool()
def get_birth_profile(client_id: int) -> dict:
    with SessionLocal() as db:
        profile = db.scalar(select(BirthProfile).where(BirthProfile.client_id == client_id))
        if profile is None: raise ValueError("birth profile not found")
        return birth_profile_to_dict(profile)


@mcp.tool()
def set_sanmeigaku_chart(client_id: int, year_pillar: str | None = None, month_pillar: str | None = None, day_pillar: str | None = None, center_star: str | None = None, north_star: str | None = None, east_star: str | None = None, south_star: str | None = None, west_star: str | None = None, early_star: str | None = None, middle_star: str | None = None, late_star: str | None = None, tenchusatsu: str | None = None, calculation_source: str | None = None, calculation_version: str | None = None, notes: str | None = None) -> dict:
    payload = SanmeigakuChartCreate(year_pillar=year_pillar, month_pillar=month_pillar, day_pillar=day_pillar, center_star=center_star, north_star=north_star, east_star=east_star, south_star=south_star, west_star=west_star, early_star=early_star, middle_star=middle_star, late_star=late_star, tenchusatsu=tenchusatsu, calculation_source=calculation_source, calculation_version=calculation_version, notes=notes)
    with SessionLocal() as db:
        if db.get(Client, client_id) is None: raise ValueError("client not found")
        chart = db.scalar(select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id))
        if chart is None:
            chart = SanmeigakuChart(client_id=client_id, **payload.model_dump()); db.add(chart)
        else:
            for field, value in payload.model_dump().items(): setattr(chart, field, value)
        db.commit(); db.refresh(chart); return sanmeigaku_chart_to_dict(chart)


@mcp.tool()
def get_sanmeigaku_chart(client_id: int) -> dict:
    with SessionLocal() as db:
        chart = db.scalar(select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id))
        if chart is None: raise ValueError("sanmeigaku chart not found")
        return sanmeigaku_chart_to_dict(chart)


@mcp.tool()
def add_reading(client_id: int, theme: str | None = None, consultation: str | None = None, methods: str | None = None, result: str | None = None, advice: str | None = None, follow_up: str | None = None, private_notes: str | None = None, reading_at: str | None = None) -> dict:
    parsed_at = datetime.fromisoformat(reading_at) if reading_at else datetime.now(timezone.utc)
    payload = ReadingCreate(reading_at=parsed_at, theme=theme, consultation=consultation, methods=methods, result=result, advice=advice, follow_up=follow_up, private_notes=private_notes)
    with SessionLocal() as db:
        if db.get(Client, client_id) is None: raise ValueError("client not found")
        reading = Reading(client_id=client_id, **payload.model_dump()); db.add(reading); db.commit(); db.refresh(reading)
        return reading_to_dict(reading)


@mcp.tool()
def list_readings(client_id: int, limit: int = 20) -> list[dict]:
    limit = max(1, min(limit, 100))
    with SessionLocal() as db:
        readings = db.scalars(select(Reading).where(Reading.client_id == client_id).order_by(Reading.reading_at.desc(), Reading.id.desc()).limit(limit)).all()
        return [reading_to_dict(reading) for reading in readings]


@mcp.tool()
def get_client_context(client_id: int, reading_limit: int = 10) -> dict:
    with SessionLocal() as db:
        return build_client_context(db, client_id, reading_limit)


@mcp.tool()
def build_ai_reading_prompt(client_id: int, question: str, reading_limit: int = 10) -> dict:
    """相談者情報からAI鑑定に送るプロンプトを確認用に生成します。"""
    with SessionLocal() as db:
        context = build_client_context(db, client_id, reading_limit)
        return {"client_id": client_id, "question": question, "prompt": build_reading_prompt(context, question)}


@mcp.tool()
def generate_ai_reading(client_id: int, question: str, reading_limit: int = 10, model: str | None = None) -> dict:
    """OpenAI APIを使って相談者情報を踏まえた鑑定補助回答を生成します。"""
    with SessionLocal() as db:
        context = build_client_context(db, client_id, reading_limit)
        return generate_reading(context, question, model)


app = FastAPI(title="uranai-app", version="0.7.0")


@app.get("/", response_class=HTMLResponse)
def index():
    return """<html lang="ja"><head><meta charset="utf-8"><title>uranai-app</title></head><body style="font-family:sans-serif;max-width:760px;margin:48px auto;line-height:1.7"><h1>uranai-app</h1><p>相談者管理・算命学命式・鑑定履歴・AI鑑定補助が動作中です。</p><ul><li><a href="/docs">API操作画面</a></li><li><a href="/api/clients">相談者一覧（JSON）</a></li><li>MCP: <code>/mcp/sse</code></li></ul></body></html>"""


@app.get("/health")
def health():
    try:
        with engine.connect() as conn: conn.execute(text("SELECT 1"))
        return {"ok": True, "database": "ok"}
    except Exception as exc: raise HTTPException(status_code=503, detail="database unavailable") from exc


@app.post("/api/clients", response_model=ClientRead, status_code=201)
def api_create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    client = Client(**payload.model_dump()); db.add(client); db.commit(); db.refresh(client); return client


@app.get("/api/clients", response_model=list[ClientRead])
def api_list_clients(q: str | None = Query(default=None, max_length=255), limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    stmt = select(Client).order_by(Client.updated_at.desc()).limit(limit)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = select(Client).where(or_(Client.name.ilike(pattern), Client.name_kana.ilike(pattern), Client.phone.ilike(pattern), Client.email.ilike(pattern), Client.line_name.ilike(pattern))).order_by(Client.updated_at.desc()).limit(limit)
    return db.scalars(stmt).all()


@app.get("/api/clients/{client_id}", response_model=ClientRead)
def api_get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if client is None: raise HTTPException(status_code=404, detail="client not found")
    return client


@app.get("/api/clients/{client_id}/context")
def api_get_client_context(client_id: int, reading_limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    try: return build_client_context(db, client_id, reading_limit)
    except ValueError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/clients/{client_id}/ai/prompt")
def api_build_ai_prompt(client_id: int, payload: AIReadingRequest, db: Session = Depends(get_db)):
    try:
        context = build_client_context(db, client_id, payload.reading_limit)
        return {"client_id": client_id, "question": payload.question, "prompt": build_reading_prompt(context, payload.question)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/clients/{client_id}/ai/generate")
def api_generate_ai_reading(client_id: int, payload: AIReadingRequest, db: Session = Depends(get_db)):
    try:
        context = build_client_context(db, client_id, payload.reading_limit)
        return generate_reading(context, payload.question, payload.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {exc}") from exc


@app.patch("/api/clients/{client_id}", response_model=ClientRead)
def api_update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if client is None: raise HTTPException(status_code=404, detail="client not found")
    for field, value in payload.model_dump(exclude_unset=True).items(): setattr(client, field, value)
    db.commit(); db.refresh(client); return client


@app.delete("/api/clients/{client_id}", status_code=204)
def api_delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if client is None: raise HTTPException(status_code=404, detail="client not found")
    db.delete(client); db.commit()


@app.post("/api/clients/{client_id}/birth-profile", response_model=BirthProfileRead, status_code=201)
def api_create_birth_profile(client_id: int, payload: BirthProfileCreate, db: Session = Depends(get_db)):
    if db.get(Client, client_id) is None: raise HTTPException(status_code=404, detail="client not found")
    if db.scalar(select(BirthProfile).where(BirthProfile.client_id == client_id)) is not None: raise HTTPException(status_code=409, detail="birth profile already exists")
    profile = BirthProfile(client_id=client_id, **payload.model_dump()); db.add(profile); db.commit(); db.refresh(profile); return profile


@app.get("/api/clients/{client_id}/birth-profile", response_model=BirthProfileRead)
def api_get_birth_profile(client_id: int, db: Session = Depends(get_db)):
    profile = db.scalar(select(BirthProfile).where(BirthProfile.client_id == client_id))
    if profile is None: raise HTTPException(status_code=404, detail="birth profile not found")
    return profile


@app.patch("/api/clients/{client_id}/birth-profile", response_model=BirthProfileRead)
def api_update_birth_profile(client_id: int, payload: BirthProfileUpdate, db: Session = Depends(get_db)):
    profile = db.scalar(select(BirthProfile).where(BirthProfile.client_id == client_id))
    if profile is None: raise HTTPException(status_code=404, detail="birth profile not found")
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("birth_time_unknown") is True: updates["birth_time"] = None
    for field, value in updates.items(): setattr(profile, field, value)
    db.commit(); db.refresh(profile); return profile


@app.delete("/api/clients/{client_id}/birth-profile", status_code=204)
def api_delete_birth_profile(client_id: int, db: Session = Depends(get_db)):
    profile = db.scalar(select(BirthProfile).where(BirthProfile.client_id == client_id))
    if profile is None: raise HTTPException(status_code=404, detail="birth profile not found")
    db.delete(profile); db.commit()


@app.post("/api/clients/{client_id}/sanmeigaku-chart", response_model=SanmeigakuChartRead, status_code=201)
def api_create_sanmeigaku_chart(client_id: int, payload: SanmeigakuChartCreate, db: Session = Depends(get_db)):
    if db.get(Client, client_id) is None: raise HTTPException(status_code=404, detail="client not found")
    if db.scalar(select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id)) is not None: raise HTTPException(status_code=409, detail="sanmeigaku chart already exists")
    chart = SanmeigakuChart(client_id=client_id, **payload.model_dump()); db.add(chart); db.commit(); db.refresh(chart); return chart


@app.get("/api/clients/{client_id}/sanmeigaku-chart", response_model=SanmeigakuChartRead)
def api_get_sanmeigaku_chart(client_id: int, db: Session = Depends(get_db)):
    chart = db.scalar(select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id))
    if chart is None: raise HTTPException(status_code=404, detail="sanmeigaku chart not found")
    return chart


@app.patch("/api/clients/{client_id}/sanmeigaku-chart", response_model=SanmeigakuChartRead)
def api_update_sanmeigaku_chart(client_id: int, payload: SanmeigakuChartUpdate, db: Session = Depends(get_db)):
    chart = db.scalar(select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id))
    if chart is None: raise HTTPException(status_code=404, detail="sanmeigaku chart not found")
    for field, value in payload.model_dump(exclude_unset=True).items(): setattr(chart, field, value)
    db.commit(); db.refresh(chart); return chart


@app.delete("/api/clients/{client_id}/sanmeigaku-chart", status_code=204)
def api_delete_sanmeigaku_chart(client_id: int, db: Session = Depends(get_db)):
    chart = db.scalar(select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id))
    if chart is None: raise HTTPException(status_code=404, detail="sanmeigaku chart not found")
    db.delete(chart); db.commit()


@app.post("/api/clients/{client_id}/readings", response_model=ReadingRead, status_code=201)
def api_create_reading(client_id: int, payload: ReadingCreate, db: Session = Depends(get_db)):
    if db.get(Client, client_id) is None: raise HTTPException(status_code=404, detail="client not found")
    data = payload.model_dump()
    if data["reading_at"] is None: data["reading_at"] = datetime.now(timezone.utc)
    reading = Reading(client_id=client_id, **data); db.add(reading); db.commit(); db.refresh(reading); return reading


@app.get("/api/clients/{client_id}/readings", response_model=list[ReadingRead])
def api_list_readings(client_id: int, limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    if db.get(Client, client_id) is None: raise HTTPException(status_code=404, detail="client not found")
    return db.scalars(select(Reading).where(Reading.client_id == client_id).order_by(Reading.reading_at.desc(), Reading.id.desc()).limit(limit)).all()


@app.get("/api/clients/{client_id}/readings/{reading_id}", response_model=ReadingRead)
def api_get_reading(client_id: int, reading_id: int, db: Session = Depends(get_db)):
    reading = db.scalar(select(Reading).where(Reading.id == reading_id, Reading.client_id == client_id))
    if reading is None: raise HTTPException(status_code=404, detail="reading not found")
    return reading


@app.patch("/api/clients/{client_id}/readings/{reading_id}", response_model=ReadingRead)
def api_update_reading(client_id: int, reading_id: int, payload: ReadingUpdate, db: Session = Depends(get_db)):
    reading = db.scalar(select(Reading).where(Reading.id == reading_id, Reading.client_id == client_id))
    if reading is None: raise HTTPException(status_code=404, detail="reading not found")
    for field, value in payload.model_dump(exclude_unset=True).items(): setattr(reading, field, value)
    db.commit(); db.refresh(reading); return reading


@app.delete("/api/clients/{client_id}/readings/{reading_id}", status_code=204)
def api_delete_reading(client_id: int, reading_id: int, db: Session = Depends(get_db)):
    reading = db.scalar(select(Reading).where(Reading.id == reading_id, Reading.client_id == client_id))
    if reading is None: raise HTTPException(status_code=404, detail="reading not found")
    db.delete(reading); db.commit()


app.mount("/mcp", mcp.sse_app(mount_path="/mcp"))
