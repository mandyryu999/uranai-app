from datetime import date

from lunar_python import Solar

GAN = "甲乙丙丁戊己庚辛壬癸"

# 五行番号: 木0 火1 土2 金3 水4
GAN_ELEMENT = {
    "甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2,
    "己": 2, "庚": 3, "辛": 3, "壬": 4, "癸": 4,
}
GAN_YANG = {g: i % 2 == 0 for i, g in enumerate(GAN)}

# 二十八元。数値は節入りからの「日間」。残りは本元。
HIDDEN_STEMS = {
    "子": [(None, 0), (None, 0), ("癸", None)],
    "丑": [("癸", 9), ("辛", 3), ("己", None)],
    "寅": [("戊", 7), ("丙", 7), ("甲", None)],
    "卯": [(None, 0), (None, 0), ("乙", None)],
    "辰": [("乙", 9), ("癸", 3), ("戊", None)],
    "巳": [("戊", 5), ("庚", 9), ("丙", None)],
    "午": [(None, 0), ("己", 19), ("丁", None)],
    "未": [("丁", 9), ("乙", 3), ("己", None)],
    "申": [("戊", 10), ("壬", 3), ("庚", None)],
    "酉": [(None, 0), (None, 0), ("辛", None)],
    "戌": [("辛", 9), ("丁", 3), ("戊", None)],
    "亥": [(None, 0), ("甲", 12), ("壬", None)],
}

# lunar-python の十二運名称（簡体字）から算命学の十二大従星へ変換。
STAGE_TO_STAR = {
    "胎": "天報星",
    "养": "天印星",
    "长生": "天貴星",
    "沐浴": "天恍星",
    "冠带": "天南星",
    "临官": "天禄星",
    "帝旺": "天将星",
    "衰": "天堂星",
    "病": "天胡星",
    "死": "天極星",
    "墓": "天庫星",
    "绝": "天馳星",
}


def major_star(day_gan: str, target_gan: str) -> str:
    """日干と対象干の相生・相剋・陰陽から十大主星を返す。"""
    de = GAN_ELEMENT[day_gan]
    te = GAN_ELEMENT[target_gan]
    same_polarity = GAN_YANG[day_gan] == GAN_YANG[target_gan]

    if de == te:
        return "貫索星" if same_polarity else "石門星"
    if (de + 1) % 5 == te:  # 日干が対象を生じる
        return "鳳閣星" if same_polarity else "調舒星"
    if (de + 2) % 5 == te:  # 日干が対象を剋す
        return "禄存星" if same_polarity else "司禄星"
    if (te + 2) % 5 == de:  # 対象が日干を剋す
        return "車騎星" if same_polarity else "牽牛星"
    if (te + 1) % 5 == de:  # 対象が日干を生じる
        return "龍高星" if same_polarity else "玉堂星"
    raise ValueError("unsupported stem relation")


def selected_hidden_stem(zhi: str, days_from_jie: int) -> str:
    """節入り日を0日として二十八元の初元・中元・本元を選ぶ。"""
    remaining = max(0, days_from_jie)
    entries = HIDDEN_STEMS[zhi]
    for stem, duration in entries:
        if stem is None:
            continue
        if duration is None:
            return stem
        if remaining <= duration:
            return stem
        remaining -= duration
    for stem, _ in reversed(entries):
        if stem:
            return stem
    raise ValueError(f"hidden stem not found for {zhi}")


def calculate_chart(birth_date: date) -> dict:
    """生年月日から標準的な算命学命式（陰占・陽占・天中殺）を算出する。"""
    # 算命学は日単位を基本とするため正午で固定し、23時の日替わり流派差を避ける。
    solar = Solar.fromYmdHms(birth_date.year, birth_date.month, birth_date.day, 12, 0, 0)
    lunar = solar.getLunar()
    eight = lunar.getEightChar()

    year_pillar = eight.getYear()
    month_pillar = eight.getMonth()
    day_pillar = eight.getDay()

    year_gan, year_zhi = year_pillar[0], year_pillar[1]
    month_gan, month_zhi = month_pillar[0], month_pillar[1]
    day_gan, day_zhi = day_pillar[0], day_pillar[1]

    prev_jie = lunar.getPrevJie(True)
    if prev_jie is None:
        raise ValueError("previous solar term could not be determined")
    jie_solar = prev_jie.getSolar()
    jie_date = date(jie_solar.getYear(), jie_solar.getMonth(), jie_solar.getDay())
    days_from_jie = (birth_date - jie_date).days

    year_hidden = selected_hidden_stem(year_zhi, days_from_jie)
    month_hidden = selected_hidden_stem(month_zhi, days_from_jie)
    day_hidden = selected_hidden_stem(day_zhi, days_from_jie)

    try:
        early_star = STAGE_TO_STAR[eight.getYearDiShi()]
        middle_star = STAGE_TO_STAR[eight.getMonthDiShi()]
        late_star = STAGE_TO_STAR[eight.getDayDiShi()]
    except KeyError as exc:
        raise ValueError(f"unknown twelve-stage value: {exc}") from exc

    return {
        "year_pillar": year_pillar,
        "month_pillar": month_pillar,
        "day_pillar": day_pillar,
        "north_star": major_star(day_gan, year_gan),
        "south_star": major_star(day_gan, month_gan),
        "east_star": major_star(day_gan, year_hidden),
        "center_star": major_star(day_gan, month_hidden),
        "west_star": major_star(day_gan, day_hidden),
        "early_star": early_star,
        "middle_star": middle_star,
        "late_star": late_star,
        "tenchusatsu": eight.getDayXunKong() + "天中殺",
        "calculation_source": "auto:lunar-python + sanmeigaku standard 28-gen",
        "calculation_version": "1.0.0",
        "notes": f"自動計算。節入り={prev_jie.getName()} {jie_date.isoformat()}、節入りから{days_from_jie}日。蔵干(年/月/日)={year_hidden}/{month_hidden}/{day_hidden}",
        "calculation_detail": {
            "day_gan": day_gan,
            "days_from_jie": days_from_jie,
            "prev_jie": prev_jie.getName(),
            "prev_jie_date": jie_date.isoformat(),
            "year_hidden_stem": year_hidden,
            "month_hidden_stem": month_hidden,
            "day_hidden_stem": day_hidden,
            "year_stage": eight.getYearDiShi(),
            "month_stage": eight.getMonthDiShi(),
            "day_stage": eight.getDayDiShi(),
        },
    }
