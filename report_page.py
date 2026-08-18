"""AIを使わない算命学総合レポート画面。"""

import html

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Client, SanmeigakuChart
from report_engine import build_sanmeigaku_report

router = APIRouter()


def get_report_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _e(value) -> str:
    return html.escape(str(value or ""))


def _tags(values) -> str:
    return "".join(f'<span class="tag">{_e(v)}</span>' for v in values or [])


def _detail_card(item: dict, period: bool = False) -> str:
    context = item.get("period_text") if period else item.get("position_text")
    context_html = f'<p class="context">{_e(context)}</p>' if context else ""
    return f'''<section class="detail-card">
      <div class="detail-head"><div><div class="eyebrow">{_e(item.get('title'))}</div><h3>{_e(item.get('star') or '未登録')}</h3></div></div>
      <div class="tags">{_tags(item.get('keywords'))}</div>
      <p>{_e(item.get('text'))}</p>
      {context_html}
    </section>'''


@router.get("/admin/clients/{client_id}/sanmeigaku-report", response_class=HTMLResponse)
def sanmeigaku_report_page(client_id: int, db: Session = Depends(get_report_db)):
    """保存済み命式から、AIなしの総合レポートを表示する。"""
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="client not found")

    chart = db.scalar(select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id))
    if chart is None:
        raise HTTPException(status_code=404, detail="sanmeigaku chart not found")

    report = build_sanmeigaku_report(chart)
    client_name = _e(client.name or "相談者")
    p = report["pillars"]
    pillars = " / ".join(_e(v or "—") for v in (p["year"], p["month"], p["day"]))
    tenchusatsu = _e(p.get("tenchusatsu") or "未登録")
    core = report["core"]
    core_context_html = (
        f'<p class="context">{_e(core.get("position_text"))}</p>'
        if core.get("position_text")
        else ""
    )
    relation_cards = "".join(_detail_card(item) for item in report["relationships"])
    life_cards = "".join(_detail_card(item, period=True) for item in report["life_flow"])
    all_stars = "・".join(_e(v) for v in report["all_stars"]) or "—"
    overview = _e(report.get("overview") or "現在登録されている星の解説をもとにレポートを構成しています。")

    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{client_name}｜算命学 総合鑑定レポート</title>
<style>
:root{{font-family:Inter,"Noto Sans JP",system-ui,sans-serif;color:#241e18;background:#f3efe8}}*{{box-sizing:border-box}}body{{margin:0}}
.top{{background:#17130f;color:#fff;padding:20px 22px}}.inner,main{{max-width:980px;margin:auto}}.nav{{display:flex;gap:14px;align-items:center;flex-wrap:wrap}}.top a{{color:#eadfce;text-decoration:none;font-size:13px}}.print{{margin-left:auto;border:1px solid #b59a69;background:#8b6b2f;color:#fff;border-radius:9px;padding:8px 12px;cursor:pointer}}h1{{font-size:26px;margin:14px 0 4px}}.subtitle{{font-size:13px;color:#c9c0b5}}
main{{padding:24px 18px 52px}}.hero,.section{{background:#fff;border:1px solid #dfd6c8;border-radius:16px;padding:22px;margin-bottom:18px;box-shadow:0 3px 12px #00000008}}.hero-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:16px}}.label,.eyebrow{{font-size:12px;color:#816d4c}}.value{{font-size:17px;font-weight:700;margin-top:3px}}h2{{font-size:20px;margin:0 0 14px}}h3{{font-size:19px;margin:4px 0 0}}p{{line-height:1.85;font-size:14px;margin:10px 0 0}}.overview{{font-size:15px;line-height:1.9}}.tags{{margin:10px 0}}.tag{{display:inline-block;background:#f5efe5;border-radius:999px;padding:4px 8px;margin:2px;font-size:12px}}.details{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}.detail-card{{border:1px solid #e5ddd1;border-radius:13px;padding:16px;background:#fdfcf9}}.context{{color:#6e655b;background:#f5f1ea;border-radius:9px;padding:10px}}.stars{{font-size:14px;line-height:1.8;color:#5e554c}}.note{{font-size:12px;color:#756c63;line-height:1.7;background:#ede8e0;padding:12px;border-radius:10px}}
@media(max-width:720px){{.hero-grid,.details{{grid-template-columns:1fr}}.print{{margin-left:0}}}}
@media print{{.top{{background:#fff;color:#111;padding:0 0 16px}}.top a,.print{{display:none}}body{{background:#fff}}main{{padding:0}}.hero,.section{{box-shadow:none;break-inside:avoid}}}}
</style></head><body>
<header class="top"><div class="inner"><div class="nav"><a href="/admin">← 管理画面</a><a href="/admin/clients/{client_id}/sanmeigaku-result">星ごとの鑑定結果</a><button class="print" onclick="window.print()">印刷・PDF保存</button></div><h1>{client_name} さんの算命学 総合鑑定レポート</h1><div class="subtitle">AIを使わず、保存済み命式と固定ルールから作成</div></div></header>
<main>
<section class="hero"><h2>命式概要</h2><div class="hero-grid"><div><div class="label">年柱 / 月柱 / 日柱</div><div class="value">{pillars}</div></div><div><div class="label">天中殺</div><div class="value">{tenchusatsu}</div></div></div></section>
<section class="section"><h2>総合概要</h2><p class="overview">{overview}</p><div class="tags">{_tags(report['keywords'])}</div><div class="stars">命盤に表れている星：{all_stars}</div></section>
<section class="section"><h2>本質・自分らしさ</h2><div class="eyebrow">中央</div><h3>{_e(core.get('star') or '未登録')}</h3><div class="tags">{_tags(core.get('keywords'))}</div><p>{_e(core.get('text'))}</p>{core_context_html}</section>
<section class="section"><h2>人間関係・社会での表れ方</h2><div class="details">{relation_cards}</div></section>
<section class="section"><h2>人生の流れ ― 初年期・中年期・晩年期</h2><div class="details">{life_cards}</div></section>
<div class="note">{_e(report['basis_note'])} 現段階では、登録済みの星と位置・時期の固定解説を組み合わせたレポートです。今後、検証済みの組み合わせルールを追加することで、さらに詳しい総合鑑定へ拡張できます。</div>
</main></body></html>'''
