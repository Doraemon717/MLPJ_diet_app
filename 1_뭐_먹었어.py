from pathlib import Path

import pandas as pd
import streamlit as st

from sources import show_sources
from widgets import number_stepper
from charts import curve_chart, ranking_chart
from core import (
    ACTIVITY_FACTORS, INTENSITY_BOUNDS, INTENSITY_LEVELS, bmr, daily_burn, format_duration, format_serving,
    history_row, intensity_of, is_soup, judge_balance, minutes_to_burn, total_kcal,
)

DATA = Path(__file__).resolve().parent.parent / "data"
FOOD_CSV, MET_CSV = DATA / "food_calories.csv", DATA / "exercise_met.csv"
MANUAL = -1  # "목록에 없음"을 뜻하는 선택값

st.title("🍽️ 뭐 먹었어?")
st.caption("오늘 먹은 걸 알려 주시면, 운동을 얼마나 해야 하는지 알려드릴게요.")


@st.cache_data
def load(path: Path) -> pd.DataFrame:
    """data/ 폴더의 CSV를 읽습니다 (음식: food_name·category·serving·kcal / 운동: exercise·met)."""
    return pd.read_csv(path)


foods = load(FOOD_CSV) if FOOD_CSV.exists() else None
st.session_state.setdefault("items", [])
st.session_state.setdefault("history", [])
st.session_state.setdefault("food_count", 1.0)
st.session_state.setdefault("manual_kcal", 0.0)


def drop_result():
    """입력(몸 정보·먹은 음식)이 바뀌면 이전 결과를 지웁니다. 바뀐 입력과 어긋난 결과가 화면에 남지 않게 하기 위해서입니다."""
    st.session_state.pop("result", None)


def change_count(step):
    """인분 − / + 버튼의 콜백: 0.5씩 바꾸되 0.5~20 범위를 벗어나지 않게 합니다."""
    st.session_state["food_count"] = min(20.0, max(0.5, st.session_state["food_count"] + step))


def add_item():
    """'추가' 버튼의 콜백: 입력값을 검사해 먹은 음식 목록에 넣고, 입력 칸을 처음 상태로 되돌립니다."""
    state = st.session_state
    pick = state.get("food_pick")
    if foods is not None and pick is not None and pick != MANUAL:
        name, kcal = foods.iloc[pick]["food_name"], float(foods.iloc[pick]["kcal"])
    else:
        name, kcal = state.get("manual_name", ""), state["manual_kcal"]
    if not name or not name.strip():
        state["add_msg"] = "음식 이름을 입력하거나 목록에서 골라 주세요."
    elif not kcal or kcal <= 0:
        state["add_msg"] = "칼로리가 0보다 커야 합니다."
    else:
        state["items"].append({"name": name.strip(), "kcal": kcal, "count": state["food_count"]})
        state.pop("result", None)
        state["food_pick"] = None
        state["food_count"] = 1.0
        state["manual_name"] = ""
        state["manual_kcal"] = 0.0


order_col, receipt_col = st.columns([3, 2], gap="large")

# 왼쪽: 주문서 (내 몸 + 먹은 음식)
with order_col:
    with st.container(border=True):
        st.markdown("##### 🙋 내 몸")
        sex_col, activity_col = st.columns(2)
        sex = sex_col.selectbox("성별", ["남성", "여성"], on_change=drop_result)
        activity = activity_col.selectbox("평소 활동량", list(ACTIVITY_FACTORS), on_change=drop_result)
        age_col, height_col, weight_col = st.columns(3)
        with age_col:
            age = number_stepper("나이(세)", "age", default=25, low=10, high=100, step=1, fmt="%d", digits=0, on_change=drop_result)
        with height_col:
            height = number_stepper("키(cm)", "height", default=170.0, low=100.0, high=220.0, step=1.0, fmt="%.0f", digits=0, on_change=drop_result)
        with weight_col:
            weight = number_stepper("체중(kg)", "weight", default=65.0, low=30.0, high=200.0, step=0.5, fmt="%.1f", digits=1, on_change=drop_result)

    with st.container(border=True):
        st.markdown("##### 🍴 오늘 먹은 것")
        st.caption("하루 동안 먹은 걸 모두 추가해야 정확해요. 한 끼만 넣으면 실제보다 적게 나옵니다.")
        if foods is None:
            st.warning("음식 데이터(data/food_calories.csv)가 없어 직접 입력만 쓸 수 있습니다.")
        pick_col, count_col, add_col = st.columns([4, 3, 2], vertical_alignment="bottom")
        manual = foods is None
        if foods is not None:
            labels = [f"{r.food_name} ({format_serving(r.serving, r.category)}) - {r.kcal}kcal" for r in foods.itertuples()]
            picked = pick_col.selectbox(
                "음식 이름",
                list(range(len(foods))) + [MANUAL],
                index=None,
                format_func=lambda i: "찾는 음식이 없어요 (직접 입력)" if i == MANUAL else labels[i],
                placeholder="검색: 제육볶음, 삼각김밥",
                key="food_pick",
            )
            manual = picked == MANUAL
            if picked is not None and picked != MANUAL and is_soup(foods.iloc[picked]["food_name"]):
                st.caption("🍚 국물 요리는 밥이 포함되지 않은 값이에요. 밥도 드셨다면 '공깃밥'도 함께 추가해 주세요.")
        with count_col:
            st.caption("인분")
            minus_col, value_col, plus_col = st.columns([1, 1.4, 1], vertical_alignment="center", gap="small")
            count = st.session_state["food_count"]
            minus_col.button("−", key="count_minus", on_click=change_count, args=(-0.5,), disabled=count <= 0.5, width="stretch")
            value_col.markdown(f"**{count:g}** 인분")
            plus_col.button("+", key="count_plus", on_click=change_count, args=(0.5,), disabled=count >= 20.0, width="stretch")
            
        name_col, kcal_col, manual_add_col = st.columns([4, 3, 2], vertical_alignment="bottom")
        name_col.text_input("음식 이름 (직접 입력)", key="manual_name")
        kcal_col.number_input("1인분 kcal", min_value=0.0, max_value=5000.0, step=10.0, key="manual_kcal")
        manual_add_col.button("추가", on_click=add_item, type="primary", width="stretch")
 
        add_msg = st.session_state.pop("add_msg", None)
        if add_msg:
            st.warning(add_msg)

# 오른쪽: 먹은 음식 목록 + 합계 + 계산 버튼
items = st.session_state["items"]
with receipt_col:
    with st.container(border=True):
        st.markdown("##### 📝 먹은 음식 목록")
        if items:
            receipt = pd.DataFrame(items)
            receipt["소계 kcal"] = (receipt["kcal"] * receipt["count"]).round().astype(int)
            st.dataframe(
                receipt.rename(columns={"name": "음식", "count": "인분"})[["음식", "인분", "소계 kcal"]],
                hide_index=True, width="stretch",
            )
            st.metric("총 섭취 칼로리", f"{total_kcal(items):,.0f} kcal")
        else:
            st.info("아직 알려 주신 음식이 없어요. 왼쪽에서 먹은 걸 추가해 주세요.")
        intensity = st.radio(
            "운동 강도", [*INTENSITY_LEVELS, "전체"], index=1, horizontal=True, key="intensity", on_change=drop_result,
            help=f"MET(운동이 가만히 있을 때보다 몇 배 에너지를 쓰는지) 기준으로 나눴어요. "
                 f"낮음 {INTENSITY_BOUNDS[0]:g} 미만 · 중간 {INTENSITY_BOUNDS[0]:g}~{INTENSITY_BOUNDS[1]:g} 미만 · 높음 {INTENSITY_BOUNDS[1]:g} 이상. "
                 "강도가 높을수록 시간은 짧지만 힘들어요.",
        )
        settle_col, clear_col = st.columns([3, 2])
        settle = settle_col.button("얼마나 뛰지?", type="primary", width="stretch", disabled=not items or not MET_CSV.exists())
        if clear_col.button("비우기", width="stretch", disabled=not items):
            st.session_state["items"] = []
            st.session_state.pop("result", None)
            st.rerun()
        if not MET_CSV.exists():
            st.warning("운동 데이터(data/exercise_met.csv)가 없어 계산할 수 없습니다.")

if settle:
    intake = total_kcal(items)
    my_bmr = bmr(sex, weight, height, age)
    burn = daily_burn(my_bmr, activity)
    balance = judge_balance(intake, burn)
    rows = [
        minutes_to_burn(balance["excess_kcal"], weight, r.exercise, r.met)
        for r in load(MET_CSV).itertuples()
        if intensity == "전체" or intensity_of(r.met) == intensity
    ]
    if not rows:
        st.warning(f"'{intensity}' 강도의 운동이 데이터에 없어 계산할 수 없습니다. 다른 강도를 골라 주세요.")
    else:
        result = {"intake": intake, "bmr": my_bmr, "burn": burn, "factor": ACTIVITY_FACTORS[activity],
                  "intensity": intensity, **balance, "rows": rows}
        st.session_state["result"] = result
        st.session_state["history"].append(history_row(len(st.session_state["history"]) + 1, items, result))

# 계산 결과 (전체 폭)
def show_exercise_tabs(result):
    """운동별 필요 시간을 비교 막대·시간별 소모 선·표 탭으로 보여 줍니다. 증가일 때와 유지에서 더 먹은 양이 있을 때 씁니다."""
    if not any(row["minutes"] > 0 for row in result["rows"]):
        st.caption("더 먹은 양이 아주 작아서 따로 운동할 필요가 없어요.")
        return
    rank_tab, curve_tab, table_tab = st.tabs(["📊 운동별 비교", "📈 시간별 소모량", "📋 표로 보기"])
    with rank_tab:
        scope = "모든 강도" if result["intensity"] == "전체" else f"'{result['intensity']}' 강도"
        st.caption(f"{scope}의 운동 중에서 막대가 짧을수록 빨리 태웁니다. 초록색이 가장 짧게 끝나는 운동이에요. "
                   "강도가 높을수록 시간은 짧지만 힘들어요. 다른 운동도 보고 싶으면 위에서 운동 강도를 바꿔 보세요.")
        st.altair_chart(ranking_chart(result["rows"]), theme=None, width="stretch")
    with curve_tab:
        st.caption("운동 시간이 지날수록 소모 칼로리가 쌓입니다. 선이 목표선과 만나는 점이 필요한 시간입니다.")
        st.altair_chart(curve_chart(result["rows"], result["excess_kcal"]), theme=None, width="stretch")
    with table_tab:
        table = pd.DataFrame(result["rows"]).sort_values("minutes")
        table["필요 시간"] = table["minutes"].map(format_duration)
        st.dataframe(table.rename(columns={"exercise": "운동"})[["운동", "필요 시간"]], hide_index=True, width="stretch")


result = st.session_state.get("result")
if result:
    st.divider()
    st.subheader("🏃 이만큼 뛰세요")
    m1, m2, m3 = st.columns(3)
    m1.metric("먹은 칼로리", f"{result['intake']:,.0f} kcal")
    m2.metric("하루 소모량", f"{result['burn']:,.0f} kcal", help=f"기초대사량 {result['bmr']:,.0f} kcal × 활동 계수 {result['factor']}")
    optional = result["status"] == "유지" and result["excess_kcal"] > 0
    m3.metric("더 태우면 좋은 칼로리" if optional else "더 태워야 할 칼로리", f"{result['excess_kcal']:,.0f} kcal")
    st.caption("하루 소모량은 '평소 활동량' 선택에 따라 달라져서, 활동량을 바꾸면 결과도 달라질 수 있어요. "
               "섭취와 하루 소모량의 차이가 ±100 kcal 이내면 '유지'로 봐요. 유지여도 더 먹은 만큼은 그대로 계산해서 보여 드려요.")
    if result["status"] == "증가":
        st.error(f"🔴 이대로면 체중이 **늘어요**. 하루 소모량보다 약 {result['excess_kcal']:,.0f} kcal 더 먹었어요. 운동으로 태워야 해요.")
        show_exercise_tabs(result)
    elif result["status"] == "유지":
        if result["excess_kcal"] > 0:
            st.info(f"🔵 **체중 유지** 상태예요. 따로 뛰지 않아도 괜찮아요. 더 확실히 균형을 맞추고 싶다면 약 {result['excess_kcal']:,.0f} kcal만 더 태우면 돼요.")
            show_exercise_tabs(result)
        else:
            st.info("🔵 **체중 유지** 상태예요. 따로 뛰지 않아도 괜찮아요.")
    else:
        if result["intake"] < result["bmr"]:
            st.warning(
                f"⚠️ 기초대사량({result['bmr']:,.0f} kcal)보다 적게 드셨어요. 하루 전체를 입력했는지 확인해 주세요. "
                "실제로 이렇게 적게 먹는 건 건강에 좋지 않을 수 있어요."
            )
        else:
            st.success("🟢 **체중 감량** 상태예요. 뛰지 않아도 돼요!")

# 내 기록 (이력)
st.divider()
st.subheader("📒 내 기록")
history = st.session_state["history"]
if history:
    st.caption("'얼마나 뛰지?'를 누를 때마다 한 줄씩 쌓입니다. 야식·간식을 더해 가며 뛰어야 할 시간이 얼마나 늘어나는지 비교해 보세요.")
    table = pd.DataFrame(history)
    st.dataframe(
        table, hide_index=True, width="stretch",
        column_config={
            "소모 필요 kcal": st.column_config.ProgressColumn(
                "소모 필요 kcal", format="%d kcal", min_value=0, max_value=max(int(table["소모 필요 kcal"].max()), 1)
            ),
            "섭취 kcal": st.column_config.NumberColumn("섭취 kcal", format="%d"),
        },
    )
    if st.button("내역 지우기"):
        st.session_state["history"] = []
        st.rerun()
else:
    st.info("아직 기록이 없어요. 결과를 확인하면 여기에 쌓입니다.")

show_sources()
