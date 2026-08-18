"""Production application entry point.

Keeps feature wiring separate from the large admin_app module so read-only
features can be added without rewriting existing admin UI/authentication code.
"""

import html

from fastapi import Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

# Keep the large existing admin UI untouched.  Before admin_app imports its
# ADMIN_HTML constant, add one navigation button by replacing one exact,
# stable fragment in memory.  This does not change DB data or admin_ui.py.
import admin_ui

_CHART_HEAD = '<div class="card"><div class="card-head"><h2>算命学命式</h2><button class="secondary small" onclick="openChartModal()">登録・編集</button></div><div id="chartCard"></div></div>'
_CHART_HEAD_WITH_RESULT = '<div class="card"><div class="card-head"><h2>算命学命式</h2><div><button class="gold small" onclick="if(selectedId)window.location.href=\'/admin/clients/\'+selectedId+\'/sanmeigaku-result\';else alert(\'相談者を選択してください\')">鑑定結果を見る</button> <button class="secondary small" onclick="openChartModal()">登録・編集</button></div></div><div id="chartCard"></div></div>'
if _CHART_HEAD in admin_ui.ADMIN_HTML:
    admin_ui.ADMIN_HTML = admin_ui.ADMIN_HTML.replace(
        _CHART_HEAD, _CHART_HEAD_WITH_RESULT, 1
    )

from admin_app import app
from database import SessionLocal
from models import Client, SanmeigakuChart
from report_page import router as report_router
from star_meanings import explain_chart

app.include_router(report_router)


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


def _star_card(item: dict, life_star: bool = False) -> str:
    name = html.escape(item.get("name") or "—")
    label_key = "period_label" if life_star else "position_label"
    meaning_key = "period_meaning" if life_star else "position_meaning"
    label = html.escape(item.get(label_key) or "")
    place_meaning = html.escape(item.get(meaning_key) or "")
    summary = html.escape(item.get("summary") or "")
    keywords = "".join(
        f'<span class="tag">{html.escape(str(keyword))}</span>'
        for keyword in item.get("keywords", [])
    )
    kind = "十二大従星" if life_star else "十大主星"
    return f'''<section class="star-card">
      <div class="star-head"><div><span class="kind">{kind}</span><h2>{name}</h2></div><div class="place">{label}</div></div>
      <div class="tags">{keywords}</div>
      <h3>星の基本的な意味</h3><p>{summary}</p>
      <h3>この位置が表すもの</h3><p>{place_meaning}</p>
    </section>'''


@app.get("/admin/clients/{client_id}/sanmeigaku-result", response_class=HTMLResponse)
def sanmeigaku_result_page(
    client_id: int,
    db: Session = Depends(get_explanation_db),
):
    """保存済み命式からAIを使わずに鑑定結果を表示する読み取り専用ページ。"""
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="client not found")

    chart = db.scalar(
        select(SanmeigakuChart).where(SanmeigakuChart.client_id == client_id)
    )
    if chart is None:
        raise HTTPException(status_code=404, detail="sanmeigaku chart not found")

    explanation = explain_chart(chart)
    major_cards = "".join(_star_card(item) for item in explanation["major_stars"])
    life_cards = "".join(
        _star_card(item, life_star=True) for item in explanation["life_stars"]
    )
    client_name = html.escape(client.name or "相談者")
    pillars = " / ".join(
        html.escape(value or "—")
        for value in (chart.year_pillar, chart.month_pillar, chart.day_pillar)
    )
    tenchusatsu = html.escape(chart.tenchusatsu or "未登録")

    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{client_name}｜算命学 鑑定結果</title>
<style>
:root{{font-family:Inter,"Noto Sans JP",system-ui,sans-serif;color:#251f19;background:#f5f3ef}}*{{box-sizing:border-box}}body{{margin:0}}
header{{background:#17130f;color:#fff;padding:18px 22px}}header .inner,main{{max-width:980px;margin:auto}}header a{{color:#e9dfcf;text-decoration:none;font-size:13px;margin-right:14px}}h1{{font-size:24px;margin:10px 0 4px}}.sub{{color:#c8bfb3;font-size:13px}}
main{{padding:24px 18px 48px}}.summary{{background:#fff;border:1px solid #e1d9cc;border-radius:16px;padding:20px;margin-bottom:20px}}.summary-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 18px;margin-top:14px}}.label{{font-size:12px;color:#766d62}}.value{{font-weight:700;margin-top:3px}}
.section-title{{font-size:19px;margin:28px 0 12px}}.cards{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}.star-card{{background:#fff;border:1px solid #e1d9cc;border-radius:15px;padding:18px;box-shadow:0 2px 9px #00000008}}.star-head{{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}}.star-head h2{{font-size:21px;margin:4px 0 0}}.kind{{font-size:11px;color:#85672e}}.place{{font-size:12px;background:#f3ede2;border-radius:999px;padding:6px 9px;text-align:right}}.tags{{margin:12px 0}}.tag{{display:inline-block;background:#f7f2e9;border-radius:999px;padding:4px 8px;margin:2px;font-size:12px}}h3{{font-size:13px;color:#6f6458;margin:15px 0 6px}}p{{font-size:14px;line-height:1.8;margin:0}}.note{{margin-top:24px;font-size:12px;color:#776e64;line-height:1.7;background:#eee9e1;padding:12px;border-radius:10px}}
@media(max-width:720px){{.cards,.summary-grid{{grid-template-columns:1fr}}.star-head{{display:block}}.place{{display:inline-block;margin-top:8px}}}}
</style></head><body>
<header><div class="inner"><a href="/admin">← 管理画面へ戻る</a><a href="/admin/clients/{client_id}/sanmeigaku-report">総合鑑定レポートを見る</a><h1>{client_name} さんの算命学 鑑定結果</h1><div class="sub">AIを使用せず、保存されている命式と解説辞書から表示しています。</div></div></header>
<main>
<section class="summary"><strong>命式概要</strong><div class="summary-grid"><div><div class="label">年柱 / 月柱 / 日柱</div><div class="value">{pillars}</div></div><div><div class="label">天中殺</div><div class="value">{tenchusatsu}</div></div></div></section>
<h2 class="section-title">十大主星 ― 本質・人間関係・社会での表れ方</h2><div class="cards">{major_cards}</div>
<h2 class="section-title">十二大従星 ― 人生の時期ごとのエネルギー</h2><div class="cards">{life_cards}</div>
<div class="note">この画面では星ごとの基本意味を確認できます。「総合鑑定レポート」では、同じ鑑定結果を本質・社会・人間関係・人生の流れに整理して表示します。</div>
</main></body></html>'''
