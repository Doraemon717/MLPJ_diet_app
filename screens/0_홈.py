import streamlit as st

from sources import show_sources

# 아래 <style> 안은 "큰 버튼 모양" 규칙이다 (동작과는 상관없음, 모르면 건너뛰어도 된다).
# .st-key-go_eat = key가 "go_eat"인 버튼, min-height = 최소 높이, hover = 마우스를 올렸을 때
st.markdown(
    """
    <style>
    .st-key-go_eat button, .st-key-go_info button {
        min-height: 3.6rem; font-size: 1.2rem; font-weight: 700; border-radius: 0.9rem;
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }
    .st-key-go_info button { border: 2px solid #e8590c; color: #e8590c; background: #ffffff; }
    .st-key-go_eat button:hover, .st-key-go_info button:hover {
        transform: translateY(-2px); box-shadow: 0 6px 16px rgba(232, 89, 12, 0.3);
    }
    .st-key-go_info button:hover { background: #fff1e6; color: #c2410c; border-color: #c2410c; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏃 얼마나 뛰지?")
st.markdown("#### 먹은 만큼, 이만큼 뛰면 돼요.")
st.write("오늘 너무 많이 먹었나? \"얼마나 운동해야 하지?\" 막막했다면, 먹은 음식만 알려 주세요. **운동 시간**으로 바로 알려 드릴게요.")

left, right = st.columns([3, 2], gap="large")
with left:
    # 눌러야 하는 곳이 한눈에 보이도록 카드 안에 큰 버튼을 둔다 (크기·테두리는 위 style 참고)
    with st.container(border=True, key="card_eat"):
        st.markdown("#### 🍽️ 뭐 먹었는지 알려 주기")
        st.caption("먹은 음식과 내 몸 정보를 넣으면, 얼만큼 운동해야 하는지 알려 드려요.")
        if st.button("지금 시작하기  →", key="go_eat", type="primary", width="stretch"):
            st.switch_page("screens/1_뭐_먹었어.py")
    with st.container(border=True, key="card_info"):
        st.markdown("#### 🔎 이건 몇 칼로리? 찾아보기")
        st.caption("궁금한 음식과 운동의 칼로리를 미리 찾아볼 수 있어요.")
        if st.button("찾아보러 가기  →", key="go_info", width="stretch"):
            st.switch_page("screens/2_이건_몇_칼로리.py")
    st.caption("로그인이나 저장 없이 바로 써 볼 수 있어요.")
with right:
    with st.container(border=True):
        st.caption("이렇게 알려 드려요 (남성 22세 · 172cm · 68kg · 활동 적음)")
        st.code(
            "Q. 오늘 이렇게 먹었는데 얼마나 뛰지?\n"
            "   아침  삼각김밥\n"
            "   점심  제육볶음 + 공깃밥\n"
            "   간식  카페라떼\n"
            "   저녁  김밥 + 라면\n"
            "   야식  초코파이 2개\n"
            "\n"
            "A. 먹은 칼로리       2,228 kcal\n"
            "   하루 소모량       1,980 kcal\n"
            "   더 태워야 할 칼로리 248 kcal\n"
            "\n"
            "   빠르게 걷기 52분 / 하이킹 42분\n"
            "   / 조깅 35분이면 돼요 (강도: 중간)",
            language=None,
        )

show_sources(full=True)
