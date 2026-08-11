from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from mcp.server.fastmcp import FastMCP
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Client
from schemas import ClientCreate, ClientRead, ClientUpdate

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def client_to_dict(client: Client) -> dict:
    return ClientRead.model_validate(client).model_dump(mode="json")


mcp = FastMCP("uranai-app")


@mcp.tool()
def db_now() -> str:
    """データベースの現在時刻を返します。"""
    with engine.connect() as conn:
        return str(conn.execute(text("SELECT now()")).scalar())


@mcp.tool()
def create_client(
    name: str,
    name_kana: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    line_name: str | None = None,
    notes: str | None = None,
) -> dict:
    """相談者カルテを新規登録します。"""
    payload = ClientCreate(
        name=name,
        name_kana=name_kana,
        phone=phone,
        email=email,
        line_name=line_name,
        notes=notes,
    )
    with SessionLocal() as db:
        client = Client(**payload.model_dump())
        db.add(client)
        db.commit()
        db.refresh(client)
        return client_to_dict(client)


@mcp.tool()
def search_clients(query: str = "", limit: int = 20) -> list[dict]:
    """名前・ふりがな・電話番号・メール・LINE名から相談者を検索します。"""
    limit = max(1, min(limit, 100))
    with SessionLocal() as db:
        stmt = select(Client).order_by(Client.updated_at.desc()).limit(limit)
        if query.strip():
            pattern = f"%{query.strip()}%"
            stmt = (
                select(Client)
                .where(
                    or_(
                        Client.name.ilike(pattern),
                        Client.name_kana.ilike(pattern),
                        Client.phone.ilike(pattern),
                        Client.email.ilike(pattern),
                        Client.line_name.ilike(pattern),
                    )
                )
                .order_by(Client.updated_at.desc())
                .limit(limit)
            )
        return [client_to_dict(client) for client in db.scalars(stmt).all()]


app = FastAPI(title="uranai-app", version="0.2.0")


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html lang="ja"><head><meta charset="utf-8"><title>uranai-app</title></head>
    <body style="font-family:sans-serif;max-width:760px;margin:48px auto;line-height:1.7">
      <h1>uranai-app</h1>
      <p>相談者カルテ基盤が動作中です。</p>
      <ul>
        <li><a href="/docs">API操作画面</a></li>
        <li><a href="/api/clients">相談者一覧（JSON）</a></li>
        <li>MCP: <code>/mcp/sse</code></li>
      </ul>
    </body></html>
    """


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True, "database": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc


@app.post("/api/clients", response_model=ClientRead, status_code=201)
def api_create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@app.get("/api/clients", response_model=list[ClientRead])
def api_list_clients(
    q: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Client).order_by(Client.updated_at.desc()).limit(limit)
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        stmt = (
            select(Client)
            .where(
                or_(
                    Client.name.ilike(pattern),
                    Client.name_kana.ilike(pattern),
                    Client.phone.ilike(pattern),
                    Client.email.ilike(pattern),
                    Client.line_name.ilike(pattern),
                )
            )
            .order_by(Client.updated_at.desc())
            .limit(limit)
        )
    return db.scalars(stmt).all()


@app.get("/api/clients/{client_id}", response_model=ClientRead)
def api_get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="client not found")
    return client


@app.patch("/api/clients/{client_id}", response_model=ClientRead)
def api_update_client(
    client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)
):
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="client not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@app.delete("/api/clients/{client_id}", status_code=204)
def api_delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="client not found")
    db.delete(client)
    db.commit()


app.mount("/mcp", mcp.sse_app(mount_path="/mcp"))
