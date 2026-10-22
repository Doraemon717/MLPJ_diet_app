"""화면 끝에 보여 주는 데이터 출처·라이선스 표시 (CC BY-SA의 출처·변경 표시 조건 포함)."""
import streamlit as st

MET_NOTE = (
    "운동 강도(MET): 한국건강증진개발원 「보건소 모바일 헬스케어 운동」(공공누리 제4유형)과 "
    "Kaggle 「Calories Burned During Exercise and Activities」(Aadhav Vignesh, CC BY-SA 4.0 · "
    "변경: 칼로리를 체중으로 나눠 MET로 바꾸고 한국어 이름을 붙임)"
)


def show_sources(full: bool = False) -> None:
    """데이터 출처를 화면 맨 아래에 보여 줍니다. full=True면 전체 목록, 아니면 한두 줄 요약."""
    st.divider()
    if not full:
        st.caption(f"📚 데이터 출처 — 음식 칼로리: 식품의약품안전처 통합식품영양성분정보 · {MET_NOTE} · 전체 목록은 홈 화면 아래")
        return
    st.markdown("##### 📚 데이터 출처")
    st.markdown(
        "- **음식 칼로리**: 식품의약품안전처 「통합식품영양성분정보(음식·가공식품)」, 공공데이터포털\n"
        "- **한국인 평균 섭취량**: 한국보건산업진흥원 「국민영양통계」 2023년\n"
        "- **운동 강도(MET)**\n"
        "  - 한국건강증진개발원 「[보건소 모바일 헬스케어 운동](https://www.data.go.kr/data/15068730/fileData.do)」 "
        "— 공공누리 제4유형(출처표시·상업적 이용금지·변경금지), 값은 원문 그대로\n"
        "  - Kaggle 「[Calories Burned During Exercise and Activities]"
        "(https://www.kaggle.com/datasets/aadhavvignesh/calories-burned-during-exercise-and-activities)」, Aadhav Vignesh — "
        "[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). "
        "**변경:** 칼로리를 체중으로 나눠 MET로 바꾸고 한국어 이름을 붙임\n"
        "  - 두 표의 값이 다를 때는 공식 Compendium of Physical Activities와 맞춰 더 가까운 쪽을 씀(검증용, 앱 데이터 아님)\n"
        "- **소모 칼로리 모델(2단계 예정)**: Kaggle 「[Calories Burnt Prediction]"
        "(https://www.kaggle.com/datasets/ruchikakumbhar/calories-burnt-prediction)」, ruchikakumbhar — "
        "[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)"
    )
    st.caption("계산은 규칙 기반 추정치이며 의학적 조언이 아닙니다.")
