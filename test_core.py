"""core.py 테스트 — 실행: python -m pytest -q"""
import pandas as pd

import pytest

from core import ACTIVITY_FACTORS, bmr, burn_per_min, daily_burn, format_duration, format_serving, history_row, intensity_of, is_soup, judge_balance, minutes_to_burn, search_food, total_kcal

FOODS = pd.DataFrame(
    {
        "food_name": ["치킨(후라이드)", "치킨(양념)", "라면"],
        "category": ["배달", "배달", "가공식품"],
        "serving": ["1조각", "1조각", "1봉지"],
        "kcal": [250, 280, 500],
    }
)


def test_search_food_찾기():
    result = search_food(FOODS, "치킨")
    assert list(result["food_name"]) == ["치킨(후라이드)", "치킨(양념)"]


def test_search_food_결과_없음():
    assert search_food(FOODS, "피자").empty


def test_search_food_빈_검색어():
    assert search_food(FOODS, "   ").empty


def test_total_kcal_합계():
    items = [
        {"name": "치킨", "kcal": 250, "count": 2},
        {"name": "라면", "kcal": 500, "count": 1},
    ]
    assert total_kcal(items) == 1000


def test_total_kcal_빈_목록():
    assert total_kcal([]) == 0


def test_bmr_남성_여성():
    assert bmr("남성", 70, 175, 25) == pytest.approx(1673.75)
    assert bmr("여성", 60, 165, 25) == pytest.approx(1345.25)


def test_bmr_잘못된_성별():
    with pytest.raises(ValueError):
        bmr("기타", 70, 175, 25)


def test_judge_balance_세_상태():
    assert judge_balance(2000, 1600) == {"status": "증가", "excess_kcal": 400.0}
    assert judge_balance(1650, 1600) == {"status": "유지", "excess_kcal": 50.0}
    assert judge_balance(1000, 1600) == {"status": "감량", "excess_kcal": 0.0}


def test_judge_balance_경계값은_유지():
    assert judge_balance(1700, 1600)["status"] == "유지"
    assert judge_balance(1500, 1600)["status"] == "유지"


def test_minutes_to_burn_계산():
    # 분당 추가 소모 = (7 − 1) × 3.5 × 70 ÷ 200 = 7.35 → 400 ÷ 7.35 = 54.4분
    assert minutes_to_burn(400, 70, "자전거", 7.0) == {"exercise": "자전거", "minutes": 54.4}


def test_burn_per_min은_안정시_1MET를_뺀다():
    assert burn_per_min(7.0, 70) == pytest.approx(7.35)
    assert burn_per_min(3.3, 65) == pytest.approx(2.3 * 3.5 * 65 / 200)


def test_burn_per_min_MET가_1_이하면_오류():
    with pytest.raises(ValueError):
        burn_per_min(1.0, 70)


def test_minutes_to_burn_초과_없으면_0분():
    assert minutes_to_burn(0, 70, "걷기", 3.5)["minutes"] == 0.0


def test_minutes_to_burn_잘못된_값():
    with pytest.raises(ValueError):
        minutes_to_burn(400, 0, "걷기", 3.5)


def test_format_serving_음료는_ml_유지():
    assert format_serving("355ml", "음료") == "355ml"


def test_format_serving_음식의_ml는_단위_제거():
    assert format_serving("117.6ml", "튀김") == "1회 약 118"


def test_format_serving_g는_그대로():
    assert format_serving("200g", "고기") == "200g"


def test_format_duration_시간과_분():
    assert format_duration(125) == "2시간 5분"
    assert format_duration(120) == "2시간"
    assert format_duration(45) == "45분"
    assert format_duration(0) == "0분"


def test_format_duration_반올림():
    assert format_duration(59.6) == "1시간"
    assert format_duration(124.5) == "2시간 5분"


RESULT = {
    "intake": 2060.0, "status": "증가", "excess_kcal": 467.5,
    "rows": [{"exercise": "걷기", "minutes": 124.5}, {"exercise": "줄넘기", "minutes": 34.8}],
}
ITEMS = [{"name": "너구리", "kcal": 515.0, "count": 4.0}, {"name": "콜라", "kcal": 129.0, "count": 0.5}]


def test_history_row_증가():
    row = history_row(1, ITEMS, RESULT)
    assert row["회차"] == 1
    assert row["먹은 음식"] == "너구리×4, 콜라×0.5"
    assert row["섭취 kcal"] == 2060 and row["소모 필요 kcal"] == 468 and row["상태"] == "증가"
    assert row["가장 빠른 운동"] == "줄넘기 35분"
    assert row["기준 운동"] == "걷기 2시간 5분"


def test_history_row_소모할_칼로리_없으면_운동은_대시():
    result = {**RESULT, "status": "감량", "excess_kcal": 0.0}
    row = history_row(2, ITEMS, result)
    assert row["가장 빠른 운동"] == "-" and row["기준 운동"] == "-" and row["소모 필요 kcal"] == 0


def test_daily_burn_활동_계수():
    assert daily_burn(1600, "거의 안 움직여요") == pytest.approx(1920)
    assert daily_burn(1600, "보통 운동 (주 3~5회)") == pytest.approx(2480)


def test_daily_burn_활동이_많을수록_큼():
    values = [daily_burn(1600, name) for name in ACTIVITY_FACTORS]
    assert values == sorted(values) and len(set(values)) == len(values)


def test_daily_burn_잘못된_활동량():
    with pytest.raises(ValueError):
        daily_burn(1600, "초인")


def test_활동량을_넣으면_같은_섭취도_덜_초과():
    # 기초대사량만 비교하면 1911kcal 섭취는 +318 초과지만, 활동 계수 1.2를 반영하면 유지
    bmr_kcal = 1592.5
    assert judge_balance(1911, bmr_kcal)["status"] == "증가"
    assert judge_balance(1911, daily_burn(bmr_kcal, "거의 안 움직여요"))["status"] == "유지"


def test_is_soup():
    for name in ["설렁탕", "미역국", "김치찌개", "해장국", "순대국", "육개장", "감자탕"]:
        assert is_soup(name), name
    for name in ["콩나물국밥", "삼계탕", "라면", "비빔밥", "공깃밥", "김치", "치킨버거"]:
        assert not is_soup(name), name


def test_judge_balance_유지_구간에서도_더_먹은_칼로리는_그대로_계산한다():
    assert judge_balance(1950, 1911) == {"status": "유지", "excess_kcal": 39.0}
    assert judge_balance(1900, 1911) == {"status": "유지", "excess_kcal": 0.0}


def test_judge_balance_경계에서_운동량이_갑자기_뛰지_않는다():
    # 이전에는 차이 +99는 0kcal, +101은 101kcal로 갑자기 뛰었다. 이제는 이름만 바뀌고 값은 이어진다.
    below = judge_balance(1600 + 99.9, 1600)
    above = judge_balance(1600 + 100.1, 1600)
    assert below["status"] == "유지" and above["status"] == "증가"
    assert above["excess_kcal"] - below["excess_kcal"] == pytest.approx(0.2)


def test_intensity_of_경계():
    assert intensity_of(2.5) == "낮음" and intensity_of(4.9) == "낮음"
    assert intensity_of(5.0) == "중간" and intensity_of(7.9) == "중간"
    assert intensity_of(8.0) == "높음" and intensity_of(12.0) == "높음"


def test_운동_표의_모든_강도에_운동이_하나_이상_있다():
    # 강도를 골랐는데 보여 줄 운동이 없는 일이 생기지 않도록 데이터를 점검
    from pathlib import Path

    met = pd.read_csv(Path(__file__).resolve().parent / "data" / "exercise_met.csv")["met"]
    assert {intensity_of(value) for value in met} == {"낮음", "중간", "높음"}
