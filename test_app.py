"""화면 테스트 — Streamlit AppTest로 브라우저 없이 화면 동작을 확인한다. 실행: python -m pytest -q"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent
EAT = str(ROOT / "screens" / "1_뭐_먹었어.py")
INFO = str(ROOT / "screens" / "2_이건_몇_칼로리.py")


@pytest.fixture
def eat():
    """'뭐 먹었어?' 화면을 처음 상태로 연다."""
    return AppTest.from_file(EAT, default_timeout=60).run()


def button(at, label):
    return next(b for b in at.button if b.label == label)


def food_box(at):
    return next(s for s in at.selectbox if s.label == "음식 이름")


def by_key(at, key):
    return next(b for b in at.button if b.key == key)


def set_servings(at, count):
    """인분 − / + 버튼을 눌러 count(0.5 단위)로 맞춘다."""
    while at.session_state["food_count"] < count:
        by_key(at, "count_plus").click().run()
    while at.session_state["food_count"] > count:
        by_key(at, "count_minus").click().run()


def add_food(at, keyword, count=1.0):
    """음식 검색 상자에서 keyword가 든 항목을 골라 인분을 넣고 '추가'를 누른다."""
    box = food_box(at)
    box.select_index(next(i for i, option in enumerate(box.options) if keyword in option)).run()
    set_servings(at, count)
    button(at, "추가").click().run()


def metrics(at):
    return {m.label: m.value for m in at.metric}


def test_진입_파일과_모든_화면이_오류_없이_열린다():
    # 홈은 메뉴(st.navigation) 안에서만 열리므로 진입 파일(app.py)을 통해 확인한다
    for path in (str(ROOT / "app.py"), EAT, INFO):
        assert not AppTest.from_file(path, default_timeout=60).run().exception


def test_음식을_추가하면_목록과_합계가_생긴다(eat):
    add_food(eat, "너구리", 4)
    assert eat.session_state["items"] == [{"name": "너구리(얼큰한맛)", "kcal": 515.0, "count": 4.0}]
    assert metrics(eat)["총 섭취 칼로리"] == "2,060 kcal"


def test_추가하면_입력_칸이_처음_상태로_돌아간다(eat):
    add_food(eat, "너구리", 4)
    assert food_box(eat).value is None
    assert eat.session_state["food_count"] == 1.0


def test_음식을_고르지_않고_추가하면_경고만_뜬다(eat):
    button(eat, "추가").click().run()
    assert eat.warning and not eat.session_state["items"]


def test_목록에_없는_음식은_직접_입력으로_추가한다(eat):
    box = food_box(eat)
    box.select_index(len(box.options) - 1).run()
    next(t for t in eat.text_input if t.label.startswith("음식 이름")).set_value("집밥").run()
    next(n for n in eat.number_input if n.label == "1인분 kcal").set_value(600.0).run()
    button(eat, "추가").click().run()
    assert eat.session_state["items"][-1] == {"name": "집밥", "kcal": 600.0, "count": 1.0}


def test_직접_입력은_이름이나_칼로리가_비면_추가되지_않는다(eat):
    box = food_box(eat)
    box.select_index(len(box.options) - 1).run()
    button(eat, "추가").click().run()
    assert eat.warning and not eat.session_state["items"]


def test_음식이_없으면_계산_버튼이_눌리지_않는다(eat):
    assert button(eat, "얼마나 뛰지?").disabled


def test_계산하면_하루_소모량과_더_태울_칼로리가_나온다(eat):
    add_food(eat, "너구리", 4)
    button(eat, "얼마나 뛰지?").click().run()
    shown = metrics(eat)
    # 남성 25세 170cm 65kg: 기초대사량 1592.5 × 1.2 = 1911 → 2060 − 1911 = 149
    assert shown["하루 소모량"] == "1,911 kcal" and shown["더 태워야 할 칼로리"] == "149 kcal"
    assert eat.error and not eat.exception


def test_활동량이_많으면_같은_음식도_초과가_없다(eat):
    add_food(eat, "너구리", 4)
    next(s for s in eat.selectbox if s.label == "평소 활동량").select("가벼운 운동 (주 1~3회)").run()
    button(eat, "얼마나 뛰지?").click().run()
    assert metrics(eat)["더 태워야 할 칼로리"] == "0 kcal" and eat.success


def test_입력이_바뀌면_이전_결과가_지워진다(eat):
    add_food(eat, "너구리", 4)
    button(eat, "얼마나 뛰지?").click().run()
    assert "result" in eat.session_state
    add_food(eat, "후라이드치킨 한", 1)
    assert "result" not in eat.session_state
    next(n for n in eat.number_input if n.label == "체중(kg)").set_value(90.0).run()
    button(eat, "얼마나 뛰지?").click().run()
    next(n for n in eat.number_input if n.label == "체중(kg)").set_value(70.0).run()
    assert "result" not in eat.session_state


def test_기록은_계산할_때마다_쌓이고_내역_지우기로만_지워진다(eat):
    for keyword in ("라면 (", "후라이드치킨 한", "카페라떼"):
        add_food(eat, keyword)
        button(eat, "얼마나 뛰지?").click().run()
    history = eat.session_state["history"]
    assert [row["회차"] for row in history] == [1, 2, 3]
    assert history[1]["소모 필요 kcal"] > 0 and history[0]["섭취 kcal"] < history[2]["섭취 kcal"]
    button(eat, "비우기").click().run()
    assert eat.session_state["items"] == [] and len(eat.session_state["history"]) == 3
    button(eat, "내역 지우기").click().run()
    assert eat.session_state["history"] == []


def test_국물_요리를_고르면_공깃밥_안내가_뜬다(eat):
    box = food_box(eat)
    box.select_index(next(i for i, o in enumerate(box.options) if "설렁탕" in o)).run()
    assert any("공깃밥" in c.value for c in eat.caption)
    box = food_box(eat)
    box.select_index(next(i for i, o in enumerate(box.options) if "라면 (" in o)).run()
    assert not any("공깃밥" in c.value for c in eat.caption)


def test_칼로리_화면은_계산한_내_섭취량을_보여_준다(eat):
    add_food(eat, "너구리", 4)
    button(eat, "얼마나 뛰지?").click().run()
    info = AppTest.from_file(INFO, default_timeout=60)
    info.session_state["result"] = eat.session_state["result"]
    info.run()
    assert not info.exception and not info.info


def test_인분은_더하기_빼기_버튼으로_0점5씩_바뀐다(eat):
    assert eat.session_state["food_count"] == 1.0
    by_key(eat, "count_plus").click().run()
    assert eat.session_state["food_count"] == 1.5
    by_key(eat, "count_minus").click().run()
    by_key(eat, "count_minus").click().run()
    assert eat.session_state["food_count"] == 0.5
    assert by_key(eat, "count_minus").disabled and not by_key(eat, "count_plus").disabled


def test_인분은_20을_넘지_않는다(eat):
    set_servings(eat, 20.0)
    assert by_key(eat, "count_plus").disabled and eat.session_state["food_count"] == 20.0


def test_버튼으로_정한_인분이_합계에_반영된다(eat):
    add_food(eat, "라면 (", 2.5)
    assert eat.session_state["items"][-1]["count"] == 2.5
    assert metrics(eat)["총 섭취 칼로리"] == "1,165 kcal"


def test_기초대사량보다_적게_먹으면_응원_대신_주의_문구가_뜬다(eat):
    add_food(eat, "아메리카노", 1)
    button(eat, "얼마나 뛰지?").click().run()
    assert any("기초대사량" in w.value for w in eat.warning)
    assert not eat.success


def test_충분히_먹고_감량이면_주의_없이_응원한다(eat):
    add_food(eat, "너구리", 4)
    next(s for s in eat.selectbox if s.label == "평소 활동량").select("보통 운동 (주 3~5회)").run()
    button(eat, "얼마나 뛰지?").click().run()
    assert eat.success and not eat.warning


def test_결과에는_판정이_활동량에_따라_달라질_수_있다는_설명이_붙는다(eat):
    add_food(eat, "너구리", 4)
    button(eat, "얼마나 뛰지?").click().run()
    assert any("±100" in c.value for c in eat.caption)


def test_칼로리_화면의_운동_시간은_처방과_같은_식을_쓴다():
    from core import format_duration, minutes_to_burn

    info = AppTest.from_file(INFO, default_timeout=60).run()
    shown = {m.label: m.value for m in info.metric}
    # 기본 선택(후라이드치킨 한 마리 2,323kcal), 기준 체중 65kg, 첫 운동 = 걷기(보통 4.8km/h, MET 3.3)
    expected = format_duration(minutes_to_burn(2323, 65, "걷기", 3.3)["minutes"])
    assert shown["걷기(보통 4.8km/h)"] == expected


def test_홈에는_눈에_띄는_시작_버튼_두_개가_있다():
    home = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert [b.label.split()[0] for b in home.button] == ["지금", "찾아보러"]
    assert not home.exception
    next(b for b in home.button if b.key == "go_eat").click().run()
    assert not home.exception


def test_모든_화면에_눈에_보이는_출처가_있다():
    # 홈은 전체 목록(마크다운), 계산 화면 둘은 요약(캡션)에 CC BY-SA 출처·변경 표시가 있어야 한다
    home = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60).run()
    assert any("CC BY-SA 4.0" in m.value and "변경:" in m.value for m in home.markdown)
    for path in (EAT, INFO):
        page = AppTest.from_file(path, default_timeout=60).run()
        assert any("CC BY-SA 4.0" in c.value and "변경:" in c.value for c in page.caption), path


def _계산하기(excess_over_burn):
    """기본 인물(하루 소모량 1,911kcal)에 '하루 소모량 + excess_over_burn' kcal를 직접 넣고 계산한 화면을 돌려준다."""
    at = AppTest.from_file(EAT, default_timeout=60)
    at.session_state["items"] = [{"name": "시험음식", "kcal": 1911.0 + excess_over_burn, "count": 1.0}]
    at.run()
    button(at, "얼마나 뛰지?").click().run()
    return at


def test_유지_구간에서도_더_먹은_칼로리는_보여_주고_하면_좋다고_안내한다():
    at = _계산하기(49)  # 차이 +49 → 유지, 이전에는 0으로 숨겨졌다
    shown = metrics(at)
    assert shown["더 태우면 좋은 칼로리"] == "49 kcal" and not at.exception
    assert any("체중 유지" in i.value and "49" in i.value for i in at.info)
    assert [t.label for t in at.tabs] == ["📊 운동별 비교", "📈 시간별 소모량", "📋 표로 보기"]


def test_경계의_양쪽에서_더_먹은_칼로리가_이어진다():
    for over, expected in ((99, "유지"), (101, "증가")):
        at = _계산하기(over)
        shown = metrics(at)
        label = "더 태우면 좋은 칼로리" if expected == "유지" else "더 태워야 할 칼로리"
        assert shown[label] == f"{over} kcal", (over, shown)  # 99 → 99, 101 → 101 (0에서 101로 뛰지 않는다)


def test_유지이고_더_먹은_양이_전혀_없으면_운동_안내가_없다():
    at = _계산하기(-30)
    assert metrics(at)["더 태워야 할 칼로리"] == "0 kcal" and not at.tabs and not at.exception


def test_더_먹은_양이_아주_작아도_오류가_나지_않는다():
    # 0.3kcal는 줄넘기 기준 0.0분으로 반올림되어, 예전 코드라면 차트 계산에서 0으로 나눴을 값
    for tiny in (0.3, 0.6, 2):
        at = _계산하기(tiny)
        assert not at.exception, tiny


def _강도로_계산(intensity, over=149):
    """기본 인물에 하루 소모량 + over kcal를 넣고, 운동 강도를 고른 뒤 계산한 화면을 돌려준다."""
    at = AppTest.from_file(EAT, default_timeout=60)
    at.session_state["items"] = [{"name": "시험음식", "kcal": 1911.0 + over, "count": 1.0}]
    at.run()
    next(r for r in at.radio if r.label == "운동 강도").set_value(intensity).run()
    button(at, "얼마나 뛰지?").click().run()
    return at


def _운동_이름(at):
    return [row["exercise"] for row in at.session_state["result"]["rows"]]


def test_운동_강도의_기본값은_중간이다(eat):
    radio = next(r for r in eat.radio if r.label == "운동 강도")
    assert radio.value == "중간" and list(radio.options) == ["낮음", "중간", "높음", "전체"]


def test_중간_강도를_고르면_중간_운동만_계산하고_줄넘기는_빠진다():
    at = _강도로_계산("중간")
    names = _운동_이름(at)
    assert len(names) == 5 and "줄넘기(빠르게)" not in names and "조깅" in names and not at.exception


def test_강도에_따라_가장_짧게_끝나는_운동이_달라진다():
    def fastest(intensity):
        rows = _강도로_계산(intensity).session_state["result"]["rows"]
        return min(rows, key=lambda row: row["minutes"])["exercise"]

    assert fastest("높음") == "줄넘기(빠르게)"
    assert fastest("낮음") == "웨이트운동(가볍게) - 전신"
    assert fastest("전체") == "줄넘기(빠르게)"
    assert fastest("중간") in ("고정식자전거타기(보통으로)", "조깅")  # 같은 MET라 둘 다 가능
    assert len(_운동_이름(_강도로_계산("전체"))) == 11


def test_운동_강도를_바꾸면_이전_결과가_지워진다(eat):
    add_food(eat, "너구리", 4)
    button(eat, "얼마나 뛰지?").click().run()
    assert "result" in eat.session_state
    next(r for r in eat.radio if r.label == "운동 강도").set_value("높음").run()
    assert "result" not in eat.session_state


def test_기록에는_고른_강도의_운동이_들어간다():
    at = _강도로_계산("높음")
    row = at.session_state["history"][-1]
    assert row["가장 빠른 운동"].startswith("줄넘기(빠르게)") and row["기준 운동"].startswith("달리기(8km/h)")


def test_차트는_가장_짧은_시간이_동점이면_모두_강조한다():
    from charts import ranking_chart

    rows = [{"exercise": "조깅", "minutes": 22.0}, {"exercise": "자전거", "minutes": 22.0}, {"exercise": "하이킹", "minutes": 26.2}]
    spec = ranking_chart(rows).to_dict()
    data = next(iter(spec["datasets"].values()))
    assert {d["exercise"] for d in data if d["best"]} == {"조깅", "자전거"}


def test_칼로리_화면도_강도에_따라_가장_짧은_운동이_달라진다():
    info = AppTest.from_file(INFO, default_timeout=60).run()
    labels = lambda page: [m.label for m in page.metric]
    assert any("(중간)" in label for label in labels(info)) and not any("줄넘기" in label for label in labels(info))
    next(r for r in info.radio if r.label == "운동 강도").set_value("높음").run()
    assert any("줄넘기(빠르게) (높음)" in label for label in labels(info)) and not info.exception


def test_나이_키_체중은_항상_보이는_더하기_빼기_버튼으로_조절된다(eat):
    clicks = [("age_plus", "age", 26), ("age_minus", "age", 25),
              ("height_plus", "height", 171.0), ("height_minus", "height", 170.0),
              ("weight_plus", "weight", 65.5), ("weight_minus", "weight", 65.0)]
    for key, state_key, expected in clicks:
        by_key(eat, key).click().run()
        assert eat.session_state[state_key] == expected, (key, eat.session_state[state_key])
    assert not eat.exception


def test_몸_정보_버튼은_범위를_넘지_않고_끝에서는_비활성이다(eat):
    next(n for n in eat.number_input if n.label == "키(cm)").set_value(220.0).run()
    assert by_key(eat, "height_plus").disabled and not by_key(eat, "height_minus").disabled
    next(n for n in eat.number_input if n.label == "체중(kg)").set_value(30.0).run()
    assert by_key(eat, "weight_minus").disabled and eat.session_state["weight"] == 30.0


def test_몸_정보를_버튼으로_바꿔도_이전_결과가_지워진다(eat):
    add_food(eat, "너구리", 4)
    button(eat, "얼마나 뛰지?").click().run()
    assert "result" in eat.session_state
    by_key(eat, "weight_plus").click().run()
    assert "result" not in eat.session_state


def test_직접_입력과_버튼을_섞어_써도_값이_이어진다(eat):
    next(n for n in eat.number_input if n.label == "체중(kg)").set_value(72.0).run()
    by_key(eat, "weight_plus").click().run()
    assert eat.session_state["weight"] == 72.5 and not eat.exception


def test_칼로리_화면의_기준_체중도_버튼으로_바뀐다():
    info = AppTest.from_file(INFO, default_timeout=60).run()
    by_key(info, "ref_weight_plus").click().run()
    assert info.session_state["ref_weight"] == 66.0 and not info.exception
