import streamlit as st

# 사이드바 메뉴 이름·아이콘·순서를 직접 정한다. 화면 폴더 이름을 pages로 하면 Streamlit이 예전 방식으로 먼저 시작해
# 처음에 "app"만 보이므로, 폴더 이름은 screens로 둔다.
st.set_page_config(layout="wide")

screens = [
    st.Page("screens/0_홈.py", title="얼마나 뛰지?", icon="🏃", default=True),
    st.Page("screens/1_뭐_먹었어.py", title="뭐 먹었어?", icon="🍽️"),
    st.Page("screens/2_이건_몇_칼로리.py", title="이건 몇 칼로리?", icon="🔎"),
]
st.navigation(screens).run()
