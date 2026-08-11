from datetime import date, time

from lunar_python import Solar

GAN = "甲乙丙丁戊己庚辛壬癸"
GAN_ELEMENT = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 2, "庚": 3, "辛": 3, "壬": 4, "癸": 4}
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

STAGE_TO_STAR = {
    "胎": "天報星", "养": "天印星", "长生": "天貴星", "沐浴": "天恍星",
    "冠带": "天南星", "临官": "天禄星", "帝旺": "天将星", "衰": "天堂星",
    "病": "天胡星", "死": "天極星", "墓": "天庫星", "绝": "天馳星",
}


def major_star(day_gan: str, target_gan: str) -> str:
    de, te = GAN_ELEMENT[day_gan], GAN_ELEMENT[target_gan]
    same = GAN_YANG[day_gan] == GAN_YANG[target_gan]
    if de == te:
        return "貫索星" if same else "石門星"
    if (de + 1) % 5 == te:
        return "鳳閣星" if same else "調舒星"
    if (de + 2) % 5 == te:
        return "禄存星" if same else "司禄星"
    if (te + 2) % 5 == de:
        return "車騎星" if same else "牽牛星"
    if (te + 1) % 5 == de:
        return "龍高星" if same else "玉堂星"
    raise ValueError("unsupported stem relation")


def selected_hidden_stem(zhi: str, days_from_jie: int) -> str:
    remaining = max(0, days_from_jie)
    for stem, duration in HIDDEN_STEMS[zhi]:
        if stem is None:
            continue
        if duration is None or remaining <= duration:
            return stem
        remaining -= duration
    raise ValueError(f"hidden stem not found for {zhi}")


def calculate_chart(birth_date: date, birth_time: time | None = None) -> dict:
    """生年月日（節入り日は可能なら出生時刻も）から算命学命式を算出する。"""
    actual_time = birth_time or time(12, 0)
    solar = Solar.fromYmdHms(
        birth_date.year, birth_date.month, birth_date.day,
        actual_time.hour, actual_time.minute, actual_time.second,
    )
    lunar = solar.getLunar()
    eight = lunar.getEightChar()

    year_pillar, month_pillar, day_pillar = eight.getYear(), eight.getMonth(), eight.getDay()
    year_gan, year_zhi = year_pillar[0], year_pillar[1]
    month_gan, month_zhi = month_pillar[0], month_pillar[1]
    day_gan, day_zhi = day_pillar[0], day_pillar[1]

    # 二十八元は算命学の「日」単位で、直前の節入り日からの日数を使う。
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

    boundary_warning = None
    if lunar.getJie() and birth_time is None:
        boundary_warning = "節入り当日で出生時刻が不明のため、正午で暫定計算しています。出生時刻が分かれば再計算してください。"

    note_parts = [
        f"自動計算。節入り={prev_jie.getName()} {jie_date.isoformat()}、節入りから{days_from_jie}日。",
        f"蔵干(年/月/日)={year_hidden}/{month_hidden}/{day_hidden}。",
    ]
    if boundary_warning:
        note_parts.append(boundary_warning)

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
        "notes": "".join(note_parts),
        "calculation_detail": {
            "day_gan": day_gan,
            "days_from_jie": days_from_jie,
            "prev_jie": prev_jie.getName(),
            "prev_jie_date": jie_date.isoformat(),
            "birth_time_used": actual_time.isoformat(),
            "birth_time_was_unknown": birth_time is None,
            "boundary_warning": boundary_warning,
            "year_hidden_stem": year_hidden,
            "month_hidden_stem": month_hidden,
            "day_hidden_stem": day_hidden,
            "year_stage": eight.getYearDiShi(),
            "month_stage": eight.getMonthDiShi(),
            "day_stage": eight.getDayDiShi(),
        },
    }
