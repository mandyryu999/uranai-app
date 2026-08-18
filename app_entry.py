"""Production application entry point.

Keeps feature wiring separate from the large admin_app module so read-only
features can be added without rewriting existing admin UI/authentication code.
"""

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from admin_app import app
from database import SessionLocal
from models import SanmeigakuChart
from star_meanings import explain_chart


def get_explanation_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/api/clients/{client_id}/sanmeigaku-explanation")
def api_get_sanmeigaku_explanation(
    client_id: int,
    db: Session = Depends(get_explanation_db),
):
    """保存済み命式を変更せず、十大主星・十二大従星の解説だけを返す。"""
    chart = db.scalar(
        select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id)
    )
    if chart is None:
        raise HTTPException(status_code=404, detail="sanmeigaku chart not found")

    return {
        "client_id": client_id,
        "explanation": explain_chart(chart),
    }
