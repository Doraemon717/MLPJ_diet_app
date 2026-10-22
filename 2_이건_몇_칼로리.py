from pathlib import Path

import pandas as pd
import streamlit as st

from sources import show_sources
from widgets import number_stepper
from charts import value_bars
from core import INTENSITY_LEVELS, burn_per_min, format_duration, format_serving, intensity_of

DATA = Path(__file__).resolve().parent.parent / "data"

st.title("🔎 이건 몇 칼로리?")
st.caption("궁금한 음식과 운동의 칼로리를 미리 찾아보세요. 앱이 계산할 때 쓰는 데이터입니다.")


@st.cache_data
def load(name: str) -> pd.DataFrame:
    """data/ 폴더의 CSV를 읽습니다."""
    return pd.read_csv(DATA / name)


missing = [n for n in ("food_calories.csv", "exercise_met.csv", "nutrition_avg_energy.csv") if not (DATA / n).exists()]
if missing:
    st.warning(f"데이터 파일이 없습니다: {', '.join(missing)}")
    st.stop()

foods, met, avg = load("food_calories.csv"), load("exercise_met.csv"), load("nutrition_avg_energy.csv")
weight = number_stepper("기준 체중(kg)", "ref_weight", default=65.0, low=30.0, high=200.0, step=1.0, fmt="%.0f", digits=0)
tab_food, tab_exercise, tab_avg = st.tabs(["🍗 음식 칼로리", "🏃 운동별 소모", "📊 다들 얼마나 먹을까"])

# 1. 음식 칼로리
with tab_food:
    st.subheader("대표 메뉴 1회분 칼로리")
    categories = ["전체"] + sorted(foods["category"].unique())
    category = st.selectbox("분류", categories)
    shown = foods if category == "전체" else foods[foods["category"] == category]
    shown = shown.assign(이름=shown["food_name"] + " (" + [format_serving(r.serving, r.category) for r in shown.itertuples()] + ")")
    shown = shown.nlargest(20, "kcal").assign(라벨=lambda d: d["kcal"].map("{:,} kcal".format))
    st.altair_chart(value_bars(shown, "이름", "kcal", "1회분 칼로리 (kcal)", "라벨"), theme=None, width="stretch")
    st.caption(f"칼로리가 높은 순으로 최대 20개를 보여 줍니다. (전체 {len(foods)}개 중 {len(foods) if category == '전체' else (foods['category'] == category).sum()}개 해당)")

    st.markdown("##### 이 음식, 얼마나 뛰어야 해?")
    pick = st.selectbox("음식 선택", foods["food_name"], index=int(foods.index[foods["food_name"] == "후라이드치킨 한 마리"][0]) if (foods["food_name"] == "후라이드치킨 한 마리").any() else 0)
    kcal = float(foods.loc[foods["food_name"] == pick, "kcal"].iloc[0])
    intensity = st.radio("운동 강도", [*INTENSITY_LEVELS, "전체"], index=1, horizontal=True, key="food_intensity",
                         help="강도가 높은 운동일수록 시간은 짧지만 힘들어요. 강도를 바꾸면 '가장 짧게 끝나는 운동'이 달라져요.")
    per_min = met["met"].map(lambda value: burn_per_min(value, weight))
    minutes = kcal / per_min
    in_range = met["met"].map(intensity_of) == intensity if intensity != "전체" else met["met"] > 0
    walk, best = met.index[0], minutes[in_range].idxmin()
    c1, c2, c3 = st.columns(3)
    c1.metric("칼로리", f"{kcal:,.0f} kcal")
    c2.metric(met.loc[walk, "exercise"], format_duration(minutes[walk]))
    c3.metric(f"{met.loc[best, 'exercise']} ({intensity})", format_duration(minutes[best]), help="고른 강도에서 가장 짧게 끝나는 운동")
    st.caption("원본: 식품의약품안전처 통합식품영양성분정보(음식)·(가공식품)에서 추린 대표값입니다. 자세한 방법은 data/README.md를 보세요.")

# 2. 운동 소모율
with tab_exercise:
    st.subheader(f"운동 30분으로 더 태우는 칼로리 (체중 {weight:.0f}kg)")
    rate = met.assign(소모=(met["met"].map(lambda value: burn_per_min(value, weight)) * 30).round().astype(int))
    rate["라벨"] = rate["소모"].map("{:,} kcal".format)
    st.altair_chart(value_bars(rate, "exercise", "소모", "30분 소모 칼로리 (kcal)", "라벨", highlight=[rate.loc[rate["소모"].idxmax(), "exercise"]]),
                    theme=None, width="stretch")
    st.caption("초록색이 가장 많이 태우는 운동입니다. 가만히 있어도 쓰는 칼로리는 뺀, 운동으로 '더' 태우는 양입니다.")
    with st.expander("MET가 뭐예요?"):
        st.markdown(
            "**MET**는 운동이 가만히 앉아 있을 때보다 에너지를 몇 배 쓰는지 나타내는 숫자예요. "
            "걷기(보통)는 3.3, 줄넘기(보통)는 10이에요.\n\n"
            "- 운동으로 **더** 태우는 칼로리 = (MET − 1) × 3.5 × 체중(kg) ÷ 200 × 시간(분)\n"
            "- 1을 빼는 이유: 가만히 있어도 쓰는 칼로리는 이미 '하루 소모량'에 들어 있기 때문이에요.\n"
            "- 운동 이름마다 MET 값이 정해져 있어서, 같은 시간이라도 줄넘기가 걷기보다 훨씬 많이 태워요.\n"
            "- 값은 한국건강증진개발원 「보건소 모바일 헬스케어 운동」 공공데이터(공공누리 제4유형)와 Kaggle 「Calories Burned During Exercise and Activities」(Aadhav Vignesh, CC BY-SA 4.0) 표에서 가져왔어요. Kaggle 표는 칼로리를 체중으로 나눠 MET로 바꾸고 한국어 이름을 붙인 것이에요. 두 표가 서로 다르면 공식 Compendium 값과 맞춰 보고 더 가까운 쪽을 썼어요."
        )

# 3. 평균과 비교
with tab_avg:
    st.subheader("한국인 하루 평균 섭취량")
    compare = avg.rename(columns={"group": "구분", "avg_kcal": "kcal"}).assign(구분=lambda d: "평균 " + d["구분"])
    result = st.session_state.get("result")
    highlight = None
    if result:
        compare = pd.concat([compare, pd.DataFrame([{"구분": "내 섭취(최근 입력)", "kcal": round(result["intake"])}])], ignore_index=True)
        highlight = ["내 섭취(최근 입력)"]
    else:
        st.info("'뭐 먹었어?'에서 먹은 음식을 알려 주면 내 섭취량이 함께 표시됩니다.")
    compare["라벨"] = compare["kcal"].map("{:,} kcal".format)
    st.altair_chart(value_bars(compare, "구분", "kcal", "하루 에너지 섭취량 (kcal)", "라벨", highlight=highlight), theme=None, width="stretch")
    st.caption("원본: 한국보건산업진흥원 국민영양통계 2023년 성별 평균 에너지 섭취량(하루 기준). 내 섭취량은 입력한 음식의 합계이며, 하루 전체가 아닐 수 있습니다.")

show_sources()
