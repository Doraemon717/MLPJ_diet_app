"""입력 칸 양옆에 항상 보이는 −/+ 버튼을 붙이는 화면 부품.

Streamlit 숫자 입력칸의 내장 −/+ 버튼은 칸이 좁거나 PC에서 마우스를 올리기 전에는 보이지 않는다.
어떤 기기·브라우저에서도 보이도록 버튼을 따로 만들고, 겹치지 않게 내장 버튼은 CSS로 숨긴다.
"""
import streamlit as st


# −/+ 버튼을 눌렀을 때 실행된다: 값에 step을 더하고(빼고), low~high 범위를 넘지 않게 자른다.
# round(..., digits)는 0.1 + 0.2 = 0.30000000000000004 같은 계산 오차를 없애려는 것.
def _bump(key: str, step: float, low: float, high: float, digits: int, on_change) -> None:
    """−/+ 버튼의 콜백: 값을 step만큼 바꾸되 low~high 범위를 벗어나지 않게 하고, 부동소수점 오차는 digits 자리로 정리한다."""
    value = round(st.session_state[key] + step, digits)
    st.session_state[key] = min(high, max(low, value))
    if on_change is not None:
        on_change()


def number_stepper(label, key, *, default, low, high, step, fmt, digits, on_change=None):
    """[−] [숫자 입력칸] [+] 한 줄. 입력칸에 직접 쓸 수도 있고, 버튼은 항상 보인다. 현재 값을 돌려준다."""
    # 1) 처음 한 번만 기본값을 보관함(session_state)에 넣는다
    st.session_state.setdefault(key, default)
    # 2) 화면 모양을 정하는 CSS (동작과는 상관없음): 내장 −/+ 숨기기, 줄바꿈 막기, 입력칸이 남는 폭 쓰기
    st.markdown(  # 내장 −/+ 버튼은 숨기고, 버튼 줄은 줄바꿈 없이 입력칸이 남는 폭을 쓰게 한다
        f"<style>.st-key-{key} [data-testid='stNumberInputStepUp'], "
        f".st-key-{key} [data-testid='stNumberInputStepDown'] {{ display: none; }}"
        f".st-key-{key}_row {{ flex-wrap: nowrap !important; gap: 0.25rem; }}"
        f".st-key-{key}_row [data-testid='stNumberInput'] {{ flex: 1 1 auto; min-width: 0; }}"
        f".st-key-{key}_row button {{ min-width: 2.2rem; padding-left: 0.4rem; padding-right: 0.4rem; }}</style>",
        unsafe_allow_html=True,
    )
    # 3) [−] 입력칸 [+]를 가로 한 줄에 놓는다. 버튼을 누르면 위의 _bump가 보관함 값을 바꾸고, 입력칸은 같은 key라서 그 값을 바로 보여 준다
    value = st.session_state[key]
    args_for = lambda sign: (key, sign * step, low, high, digits, on_change)
    with st.container(horizontal=True, vertical_alignment="bottom", wrap=False, key=f"{key}_row"):
        st.button("−", key=f"{key}_minus", on_click=_bump, args=args_for(-1), disabled=value <= low, width="content")
        number = st.number_input(label, min_value=low, max_value=high, step=step, format=fmt, key=key, on_change=on_change)
        st.button("+", key=f"{key}_plus", on_click=_bump, args=args_for(1), disabled=value >= high, width="content")
    return number
