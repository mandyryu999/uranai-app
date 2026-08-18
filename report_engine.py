"""AIを使わない算命学レポート組み立てロジック。

既存のSanmeigakuChartを読み、確定済み辞書と組み合わせルールだけを使って
再現性のあるレポートデータを作る。DBへの書き込みは行わない。
"""

from star_meanings import explain_chart
from combination_interpretations import get_center_east_interpretation


def _major_by_position(explanation: dict) -> dict[str, dict]:
    return {item.get("position"): item for item in explanation.get("major_stars", []) if item.get("position")}


def _life_by_period(explanation: dict) -> dict[str, dict]:
    return {item.get("period"): item for item in explanation.get("life_stars", []) if item.get("period")}


def _major_text(item: dict | None) -> str:
    if not item:
        return "この項目の星はまだ登録されていません。"
    return item.get("position_interpretation") or item.get("summary") or ""


def _life_text(item: dict | None) -> str:
    if not item:
        return "この項目の星はまだ登録されていません。"
    return item.get("period_interpretation") or item.get("summary") or ""


def build_sanmeigaku_report(chart) -> dict:
    """保存済み命式から、AIなしの構造化鑑定レポートを返す。"""
    explanation = explain_chart(chart)
    major = _major_by_position(explanation)
    life = _life_by_period(explanation)
    center, north, east, south, west = (major.get(k) for k in ("center", "north", "east", "south", "west"))
    early, middle, late = (life.get(k) for k in ("early", "middle", "late"))

    core = {"title": "本質・自分らしさ", "star": center.get("name") if center else None, "text": _major_text(center), "position_text": center.get("position_meaning") if center else None, "keywords": center.get("keywords", []) if center else []}
    relationships = [
        {"title": "目上・親・精神面", "star": north.get("name") if north else None, "text": _major_text(north), "position_text": north.get("position_meaning") if north else None, "keywords": north.get("keywords", []) if north else []},
        {"title": "社会・仕事・友人", "star": east.get("name") if east else None, "text": _major_text(east), "position_text": east.get("position_meaning") if east else None, "keywords": east.get("keywords", []) if east else []},
        {"title": "目下・子ども・未来", "star": south.get("name") if south else None, "text": _major_text(south), "position_text": south.get("position_meaning") if south else None, "keywords": south.get("keywords", []) if south else []},
        {"title": "家庭・配偶者・身近な関係", "star": west.get("name") if west else None, "text": _major_text(west), "position_text": west.get("position_meaning") if west else None, "keywords": west.get("keywords", []) if west else []},
    ]
    life_flow = [
        {"title": "初年期", "star": early.get("name") if early else None, "text": _life_text(early), "period_text": early.get("period_meaning") if early else None, "keywords": early.get("keywords", []) if early else []},
        {"title": "中年期", "star": middle.get("name") if middle else None, "text": _life_text(middle), "period_text": middle.get("period_meaning") if middle else None, "keywords": middle.get("keywords", []) if middle else []},
        {"title": "晩年期", "star": late.get("name") if late else None, "text": _life_text(late), "period_text": late.get("period_meaning") if late else None, "keywords": late.get("keywords", []) if late else []},
    ]

    center_east = get_center_east_interpretation(center.get("name") if center else None, east.get("name") if east else None)
    combinations = [center_east] if center_east else []

    present_stars = [item.get("name") for item in explanation.get("major_stars", []) + explanation.get("life_stars", []) if item.get("name")]
    keyword_order = []
    for item in explanation.get("major_stars", []) + explanation.get("life_stars", []):
        for keyword in item.get("keywords", []):
            if keyword not in keyword_order:
                keyword_order.append(keyword)

    overview_parts = []
    if center:
        overview_parts.append(f"命式の中心には{center['name']}があり、{_major_text(center)}")
    if east:
        overview_parts.append(f"社会面には{east['name']}があり、{_major_text(east)}")
    if center_east:
        overview_parts.append(center_east["text"])
    if middle:
        overview_parts.append(f"人生の中心期には{middle['name']}があり、{_life_text(middle)}")

    return {
        "pillars": {"year": getattr(chart, "year_pillar", None), "month": getattr(chart, "month_pillar", None), "day": getattr(chart, "day_pillar", None), "tenchusatsu": getattr(chart, "tenchusatsu", None)},
        "core": core,
        "relationships": relationships,
        "life_flow": life_flow,
        "combinations": combinations,
        "overview": " ".join(overview_parts),
        "all_stars": present_stars,
        "keywords": keyword_order,
        "basis_note": "このレポートは保存済み命式とアプリ内の固定鑑定ルールを組み合わせて作成しています。AIによる文章生成は使用していません。",
    }
