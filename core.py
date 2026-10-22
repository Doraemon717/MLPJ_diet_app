"""로직 모듈 — streamlit을 import하지 않는다 (pytest 테스트·3단계 API 이전용).

화면(screens/)은 입력을 넘기고 결과만 보여 주며, 계산은 모두 여기서 한다.
"""
import re

import pandas as pd


def search_food(foods: pd.DataFrame, query: str) -> pd.DataFrame:
    """음식명에 query가 포함된 행을 돌려줍니다. 빈 검색어·결과 없음이면 빈 DataFrame (US-1).

    현재 화면은 선택 상자의 자체 검색을 쓰므로 호출하지 않는다. 텍스트 검색으로 바꿀 때를 위해 남겨 둔 함수."""
    query = query.strip()
    if not query:
        return foods.iloc[0:0]
    mask = foods["food_name"].str.contains(query, regex=False, na=False)
    return foods[mask]


def format_serving(serving: str, category: str) -> str:
    """분량 표시 문자열. 음료만 ml를 그대로 쓰고, 그 밖의 ml(원본 DB의 표기 방식)는 단위를 뺀다 (US-1).

    예: ("355ml", "음료") → "355ml", ("117.6ml", "튀김") → "1회 약 118", ("200g", "고기") → "200g".
    """
    match = re.fullmatch(r"([\d.]+)ml", serving.strip())
    if match is None or category == "음료":
        return serving
    return f"1회 약 {float(match.group(1)):.0f}"


def format_duration(minutes: float) -> str:
    """분을 사람이 읽기 쉬운 시간 표기로 바꿉니다 (US-2). 예: 125 → "2시간 5분", 45 → "45분", 120 → "2시간"."""
    total = int(minutes + 0.5)  # round()는 124.5를 124로 만들어 사람이 기대하는 반올림과 다름
    hours, rest = divmod(total, 60)
    if hours == 0:
        return f"{rest}분"
    return f"{hours}시간" if rest == 0 else f"{hours}시간 {rest}분"


def total_kcal(items: list[dict]) -> float:
    """[{"name": str, "kcal": float, "count": float}, ...] 의 총 섭취 칼로리 합계 (US-1)."""
    return float(sum(item["kcal"] * item["count"] for item in items))


MAINTAIN_MARGIN_KCAL = 100  # 기초대사량과 섭취량 차이가 이 값 이내면 "유지"


def bmr(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    """기초대사량(kcal/일). Mifflin-St Jeor 식 (US-2). sex는 "남성" 또는 "여성"."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex == "남성":
        return base + 5
    if sex == "여성":
        return base - 161
    raise ValueError(f"성별은 '남성' 또는 '여성'이어야 합니다: {sex}")


ACTIVITY_FACTORS = {
    "거의 안 움직여요": 1.2,
    "가벼운 운동 (주 1~3회)": 1.375,
    "보통 운동 (주 3~5회)": 1.55,
}  # 기초대사량에 곱해 하루 소모량을 구하는 일반적인 활동 계수


def daily_burn(bmr_kcal: float, activity: str) -> float:
    """하루 총 소모량(kcal) = 기초대사량 × 활동 계수 (US-2). activity는 ACTIVITY_FACTORS의 키."""
    if activity not in ACTIVITY_FACTORS:
        raise ValueError(f"알 수 없는 활동량입니다: {activity}")
    return bmr_kcal * ACTIVITY_FACTORS[activity]


def is_soup(food_name: str) -> bool:
    """국·탕·찌개·육개장처럼 밥이 따로 필요한 국물 요리인지 이름으로 판별합니다. 밥이 들어 있는 국밥류·삼계탕은 제외."""
    return food_name.endswith(("국", "탕", "찌개", "개장")) and not food_name.endswith(("국밥", "삼계탕"))


def judge_balance(intake_kcal: float, burn_kcal: float) -> dict:
    """섭취량과 하루 소모량(daily_burn 결과)을 비교해 {"status": "증가"|"유지"|"감량", "excess_kcal": float} (US-2).

    상태 이름: 차이(섭취 − 소모)가 +MAINTAIN_MARGIN_KCAL 초과면 "증가", -MAINTAIN_MARGIN_KCAL 미만이면 "감량", 그 사이는 "유지".
    excess_kcal(더 먹은 칼로리)은 상태와 상관없이 차이가 플러스일 때 그 차이이고, 마이너스면 0이다.
    그래서 유지 구간의 경계(+100 직전·직후)에서 운동량이 갑자기 0에서 100으로 뛰지 않고 연속으로 이어진다.
    """
    diff = intake_kcal - burn_kcal
    if diff > MAINTAIN_MARGIN_KCAL:
        status = "증가"
    elif diff < -MAINTAIN_MARGIN_KCAL:
        status = "감량"
    else:
        status = "유지"
    return {"status": status, "excess_kcal": float(max(diff, 0.0))}


INTENSITY_LEVELS = ("낮음", "중간", "높음")
INTENSITY_BOUNDS = (5.0, 8.0)  # MET 5 미만=낮음, 5 이상 8 미만=중간, 8 이상=높음 (이 경계는 AI가 임의로 나눈 값)


def intensity_of(met: float) -> str:
    """운동의 MET 값으로 강도 구간("낮음"·"중간"·"높음")을 돌려줍니다 (US-2). 경계값은 INTENSITY_BOUNDS."""
    low, high = INTENSITY_BOUNDS
    if met < low:
        return "낮음"
    return "중간" if met < high else "높음"


def burn_per_min(met: float, weight_kg: float) -> float:
    """운동으로 '추가로' 태우는 분당 칼로리 = (MET − 1) × 3.5 × 체중 ÷ 200 (US-2).

    MET는 가만히 있을 때(1MET)의 몇 배인지를 뜻한다. 하루 소모량(기초대사량 × 활동 계수)에는 운동하는 시간의
    기본 소모(1MET)가 이미 들어 있으므로, 운동으로 더 태우는 양은 (MET − 1) 기준이다.
    """
    if weight_kg <= 0 or met <= 1:
        raise ValueError("체중은 0보다, MET는 1보다 커야 합니다.")
    return (met - 1) * 3.5 * weight_kg / 200


def minutes_to_burn(excess_kcal: float, weight_kg: float, exercise: str, met: float) -> dict:
    """초과 칼로리를 소모하는 데 필요한 {"exercise": str, "minutes": float} (US-2).

    1단계: 분당 추가 소모 kcal(burn_per_min)로 나누는 규칙 계산. 2단계에서 회귀 모델로 교체하며 반환 형식은 같게 유지.
    운동 강도는 MET 표의 운동 이름(속도 등)에 이미 들어 있어 1단계에서는 따로 받지 않는다.
    """
    per_min = burn_per_min(met, weight_kg)
    if excess_kcal <= 0:
        return {"exercise": exercise, "minutes": 0.0}
    return {"exercise": exercise, "minutes": round(excess_kcal / per_min, 0)}


def history_row(round_no: int, items: list[dict], result: dict) -> dict:
    """처방 결과 한 건을 이력 표의 한 줄(dict)로 만든다 (US-3).

    result는 {"intake", "status", "excess_kcal", "rows": [{"exercise", "minutes"}, ...]} 형태.
    rows는 사용자가 고른 운동 강도의 운동만 담고, rows[0]은 그 강도에서 표의 첫 운동을 기준 운동으로 본다. 소모할 칼로리가 없으면 운동 칸은 "-"로 둔다.
    """
    foods = ", ".join(f"{item['name']}×{item['count']:g}" for item in items)
    if result["excess_kcal"] > 0:
        fastest = min(result["rows"], key=lambda row: row["minutes"])
        base = result["rows"][0]
        fastest_text = f"{fastest['exercise']} {format_duration(fastest['minutes'])}"
        base_text = f"{base['exercise']} {format_duration(base['minutes'])}"
    else:
        fastest_text = base_text = "-"
    return {
        "회차": round_no,
        "먹은 음식": foods,
        "섭취 kcal": int(result["intake"] + 0.5),
        "소모 필요 kcal": int(result["excess_kcal"] + 0.5),
        "상태": result["status"],
        "가장 빠른 운동": fastest_text,
        "기준 운동": base_text,
    }
