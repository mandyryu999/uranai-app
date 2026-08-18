"""算命学の星の意味をAIなしで返すためのルールベース辞書。

文章はアプリ独自の説明文として管理し、今後位置別・組み合わせ別の解釈を拡張する。
"""

TEN_MAJOR_STARS = {
    "貫索星": {"keywords": ["自立", "守り", "意志", "マイペース"], "summary": "自分の軸を大切にし、簡単には周囲に流されない星です。自立心と粘り強さを活かすほど力を発揮します。"},
    "石門星": {"keywords": ["協調", "仲間", "社交", "つながり"], "summary": "人との横のつながりを広げ、仲間と力を合わせることに長けた星です。対等な関係の中で力を発揮します。"},
    "鳳閣星": {"keywords": ["自然体", "表現", "伝達", "楽しさ"], "summary": "自然体で物事を伝え、人生をのびやかに味わう星です。無理をせず、自分らしい表現を続けることが魅力につながります。"},
    "調舒星": {"keywords": ["感性", "独自性", "繊細", "表現"], "summary": "鋭い感性と独自の世界観を持つ星です。一人で深く考える時間や、感性を表現できる環境が才能を育てます。"},
    "禄存星": {"keywords": ["愛情", "奉仕", "引力", "人を惹きつける"], "summary": "人に喜んでもらうことを大切にし、周囲を惹きつける力を持つ星です。愛情を循環させることで存在感が高まります。"},
    "司禄星": {"keywords": ["蓄積", "家庭", "堅実", "継続"], "summary": "身近な人や生活を大切にし、小さな積み重ねを形にしていく星です。安定した環境の中で着実に力を伸ばします。"},
    "車騎星": {"keywords": ["行動", "正義感", "スピード", "実践"], "summary": "考えるだけでなく、まず動くことで道を開く星です。率直さと行動力が強みで、目的が明確なほど力を発揮します。"},
    "牽牛星": {"keywords": ["責任", "役割", "名誉", "規律"], "summary": "任された役割をきちんと果たそうとする責任感の強い星です。社会的な立場や信頼を意識することで成長します。"},
    "龍高星": {"keywords": ["探究", "改革", "体験", "未知"], "summary": "未知の世界へ踏み出し、体験から学ぶ探究心の星です。変化を恐れず新しい価値観に触れることで可能性が広がります。"},
    "玉堂星": {"keywords": ["知性", "学習", "伝統", "継承"], "summary": "知識を学び、受け継ぎ、次へ伝えることに適した星です。じっくり理解して積み上げた知恵が大きな財産になります。"},
}

TWELVE_LIFE_STARS = {
    "天報星": {"keywords": ["変化", "多面性", "可能性"], "summary": "変化への対応力と多面的な可能性を象徴する星です。ひとつに固定しすぎず、経験の幅を広げることが活力につながります。"},
    "天印星": {"keywords": ["素直", "受容", "愛される力"], "summary": "素直さや受け取る力を象徴する星です。周囲から助けられやすく、人との自然な関わりの中で魅力が表れます。"},
    "天貴星": {"keywords": ["品性", "学び", "自尊心"], "summary": "品性と学ぶ姿勢を象徴する星です。自分なりの誇りを持ち、丁寧に経験を積むことで持ち味が育ちます。"},
    "天恍星": {"keywords": ["夢", "魅力", "感受性"], "summary": "夢や憧れ、華やかな感性を象徴する星です。理想を持つことが原動力になり、表現の場で魅力が出やすい傾向があります。"},
    "天南星": {"keywords": ["挑戦", "勢い", "前進"], "summary": "若々しい行動力と挑戦心を象徴する星です。経験を恐れず前へ出ることで、持っているエネルギーを活かせます。"},
    "天禄星": {"keywords": ["安定", "現実性", "守備力"], "summary": "安定感と現実的な判断力を象徴する星です。足元を固め、責任を持って物事を継続することで信頼につながります。"},
    "天将星": {"keywords": ["責任", "統率", "大きなエネルギー"], "summary": "十二大従星の中でも大きなエネルギーを象徴する星です。責任ある立場や、自分で決断して進む環境で力を活かしやすくなります。"},
    "天堂星": {"keywords": ["経験", "落ち着き", "支える力"], "summary": "経験を重ねた落ち着きと、人を支える力を象徴する星です。前に出るだけでなく、全体を見ながら支える役割にも適性があります。"},
    "天胡星": {"keywords": ["感性", "直感", "精神性"], "summary": "繊細な感性や直感的な世界を象徴する星です。目に見えるものだけにとらわれず、想像力を活かすことで魅力が深まります。"},
    "天極星": {"keywords": ["純粋", "受容", "精神性"], "summary": "物事を受け入れる柔らかさと純粋さを象徴する星です。執着を手放し、流れを受け止める姿勢から独特の強さが生まれます。"},
    "天庫星": {"keywords": ["探究", "集中", "整理"], "summary": "ひとつのテーマを深く掘り下げ、整理して残す力を象徴する星です。専門性を磨くほど持ち味が発揮されます。"},
    "天馳星": {"keywords": ["瞬発力", "自由", "スピード"], "summary": "素早い行動と自由な動きを象徴する星です。ひとつの場所に留まり続けるより、機動力を活かすことで力が出やすくなります。"},
}

MAJOR_POSITION_LABELS = {
    "center": "中央（本質・自分自身）",
    "north": "北方（目上・親・精神面）",
    "east": "東方（社会・仕事・友人）",
    "south": "南方（目下・子ども・未来）",
    "west": "西方（家庭・配偶者・身近な関係）",
}

LIFE_PERIOD_LABELS = {
    "early": "初年期",
    "middle": "中年期",
    "late": "晩年期",
}


def explain_major_star(star_name: str | None, position: str | None = None) -> dict | None:
    if not star_name or star_name not in TEN_MAJOR_STARS:
        return None
    data = TEN_MAJOR_STARS[star_name]
    return {"name": star_name, "position": position, "position_label": MAJOR_POSITION_LABELS.get(position), **data}


def explain_life_star(star_name: str | None, period: str | None = None) -> dict | None:
    if not star_name or star_name not in TWELVE_LIFE_STARS:
        return None
    data = TWELVE_LIFE_STARS[star_name]
    return {"name": star_name, "period": period, "period_label": LIFE_PERIOD_LABELS.get(period), **data}


def explain_chart(chart) -> dict:
    """SanmeigakuChart相当のオブジェクトから8つの星の基本解説を返す。"""
    major = []
    for position, field in (("center", "center_star"), ("north", "north_star"), ("east", "east_star"), ("south", "south_star"), ("west", "west_star")):
        item = explain_major_star(getattr(chart, field, None), position)
        if item:
            major.append(item)
    life = []
    for period, field in (("early", "early_star"), ("middle", "middle_star"), ("late", "late_star")):
        item = explain_life_star(getattr(chart, field, None), period)
        if item:
            life.append(item)
    return {"major_stars": major, "life_stars": life}
