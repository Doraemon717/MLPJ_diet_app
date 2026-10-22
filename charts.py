"""운동 결과·음식 칼로리 차트 (Altair). 계산은 core.py가 하고, 여기서는 그리기만 한다.

읽는 법 (Altair 한눈에):
- 차트 하나 = alt.Chart(표 데이터) + mark_xxx(모양: 막대·선·점·글자) + encode(표의 어느 열을 가로·세로·색에 쓸지)
- 차트 여러 개를 `+`로 이으면 한 그림 위에 겹쳐 그려진다. 예) 막대 + 막대 끝 글자 = 값이 적힌 막대
- 이 파일의 함수는 모두 같은 순서: 표 만들기 → 모양 정하기 → 겹치기 → _style로 색·격자 꾸미기
"""
import altair as alt
import pandas as pd

from core import format_duration

# 색: 선은 dataviz 기본 팔레트 슬롯 1~3(validate_palette.js 통과), 막대 강조는 앱 테마의 초록
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
ACCENT, MUTED = "#16a34a", "#b4beb8"
TEXT, TEXT_SECONDARY, GRID = "#1f2a24", "#5f6b64", "#e3e9e5"


# 모든 차트에 같은 꾸밈(배경 투명, 연한 격자, 글자색)을 입힌다. 그림 내용은 바꾸지 않는다.
def _style(chart: alt.Chart) -> alt.Chart:
    """모든 차트 공통: 흰 배경, 얇고 연한 실선 격자, 본문 글자색."""
    return (
        chart.configure(background="rgba(0,0,0,0)")
        .configure_view(stroke=None)
        .configure_axis(
            gridColor=GRID, gridWidth=1, domainColor=GRID, tickColor=GRID,
            labelColor=TEXT_SECONDARY, titleColor=TEXT_SECONDARY, labelFontSize=12, titleFontSize=12,
        )
        .configure_legend(labelColor=TEXT, labelFontSize=12)
    )


# 계산 결과(운동 이름·분)를 차트에 쓰기 좋은 표로 바꾼다: 짧은 순 정렬 + 시간(hours) + 글자 라벨 + 1등 표시(best)
def _frame(rows: list[dict]) -> pd.DataFrame:
    """처방 결과 rows([{"exercise", "minutes"}])를 필요 시간이 짧은 순의 표로 만든다."""
    df = pd.DataFrame(rows).sort_values("minutes").reset_index(drop=True)
    df["hours"] = df["minutes"] / 60
    df["label"] = df["minutes"].map(format_duration)
    df["best"] = df["minutes"] == df["minutes"].min()  # 가장 짧은 시간이 동점이면 모두 강조
    return df


def ranking_chart(rows: list[dict]) -> alt.Chart:
    """운동별 필요 시간 가로 막대. 짧은 순 정렬, 값은 막대 끝, 가장 짧은 운동만 강조색."""
    df = _frame(rows)
    # y축: 운동 이름을 필요 시간이 짧은 순으로 세로로 나열 (":N"은 글자 종류 열이라는 뜻)
    y = alt.Y("exercise:N", sort=alt.EncodingSortField("minutes"), title=None,
              axis=alt.Axis(labelLimit=240, ticks=False, domain=False))
    base = alt.Chart(df).encode(y=y)  # 막대와 글자가 같은 세로 위치를 쓰도록 공통으로 둔다
    # 막대: 길이=필요 시간 (":Q"는 숫자 열), 색은 best가 참인 가장 짧은 운동만 초록
    bars = base.mark_bar(size=18, cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        x=alt.X("hours:Q", title="필요 시간 (시간)", scale=alt.Scale(domain=[0, df["hours"].max() * 1.3])),
        color=alt.Color("best:N", scale=alt.Scale(domain=[True, False], range=[ACCENT, MUTED]), legend=None),
        tooltip=[alt.Tooltip("exercise:N", title="운동"), alt.Tooltip("label:N", title="필요 시간")],
    )
    # 막대 끝에 "41분" 같은 글자를 붙인다. 막대 + 글자를 `+`로 겹치면 값이 적힌 막대가 된다
    labels = base.mark_text(align="left", dx=6, color=TEXT, fontSize=12).encode(x="hours:Q", text="label:N")
    return _style((bars + labels).properties(height=max(120, 30 * len(df))))


def curve_chart(rows: list[dict], excess_kcal: float) -> alt.Chart:
    """시간에 따른 누적 소모 칼로리 선. 가장 빠른·중간·가장 느린 운동 3개가 목표선과 만나는 점이 필요 시간."""
    df = _frame(rows)
    # 아이디어: 운동 시간이 지날수록 태운 칼로리가 직선으로 늘어난다. 이 직선이 "목표 칼로리" 선과 만나는 점이 필요한 시간.
    df = df[df["minutes"] > 0].reset_index(drop=True)  # 초과가 아주 작아 0.0분이 된 운동은 제외(0으로 나누기 방지)
    picks = df.iloc[sorted({0, len(df) // 2, len(df) - 1})].reset_index(drop=True)  # 가장 빠른·중간·가장 느린 운동 3개만 그린다
    names = list(picks["exercise"])
    palette = [BLUE, ORANGE, AQUA][: len(names)]
    x_max = picks["hours"].max() * 1.1
    # 직선 하나는 점 두 개로 정해진다: (0시간, 0kcal)과 (끝시간, 그때까지 태운 kcal). 기울기 = 목표 kcal ÷ 필요 시간
    lines = pd.DataFrame(
        [
            {"exercise": r.exercise, "hours": h, "kcal": excess_kcal / r.hours * h}
            for r in picks.itertuples()
            for h in (0, x_max)
        ]
    )
    color = alt.Color("exercise:N", scale=alt.Scale(domain=names, range=palette),
                      legend=alt.Legend(orient="top", title=None, symbolType="stroke", symbolStrokeWidth=3))
    x = alt.X("hours:Q", title="운동 시간 (시간)", scale=alt.Scale(domain=[0, x_max], nice=False))
    y = alt.Y("kcal:Q", title="소모 칼로리 (kcal)", scale=alt.Scale(domain=[0, excess_kcal * 1.25], nice=False))
    # 아래 5개를 `+`로 겹친다: ① 운동별 직선 ② 목표 가로선 ③ 목표 글자 ④ 직선과 목표선이 만나는 점 ⑤ 점 위의 시간 글자
    line = alt.Chart(lines).mark_line(strokeWidth=2, strokeJoin="round", strokeCap="round", clip=True).encode(
        x=x, y=y, color=color, tooltip=[alt.Tooltip("exercise:N", title="운동")])
    target = alt.Chart(pd.DataFrame({"kcal": [excess_kcal]})).mark_rule(color=TEXT_SECONDARY, strokeWidth=1).encode(y=y)
    target_label = alt.Chart(pd.DataFrame({"kcal": [excess_kcal], "hours": [x_max]})).mark_text(
        align="right", dy=-8, color=TEXT_SECONDARY, fontSize=12
    ).encode(x=x, y=y, text=alt.value(f"목표 {excess_kcal:,.0f} kcal"))
    dots = alt.Chart(picks.assign(kcal=excess_kcal)).mark_point(
        filled=True, size=90, opacity=1, stroke="#ffffff", strokeWidth=2
    ).encode(x=x, y=y, color=color, tooltip=[alt.Tooltip("exercise:N", title="운동"), alt.Tooltip("label:N", title="필요 시간")])
    dot_labels = alt.Chart(picks.assign(kcal=excess_kcal)).mark_text(
        dy=-14, color=TEXT, fontSize=12, fontWeight="bold"
    ).encode(x=x, y=y, text="label:N")
    return _style((line + target + target_label + dots + dot_labels).properties(height=340))


def value_bars(df: pd.DataFrame, name: str, value: str, title: str, label: str, highlight: list | None = None) -> alt.Chart:
    """값이 큰 순으로 정렬한 가로 막대 (칼로리 구경 화면용). highlight에 든 이름만 강조색, 나머지는 회색. 값은 막대 끝에 표시."""
    df = df.copy()
    df["hl"] = df[name].isin(highlight or [])
    y = alt.Y(f"{name}:N", sort=alt.EncodingSortField(value, order="descending"), title=None,
              axis=alt.Axis(labelLimit=240, ticks=False, domain=False))
    base = alt.Chart(df).encode(y=y)
    if highlight:
        color = alt.Color("hl:N", scale=alt.Scale(domain=[True, False], range=[ACCENT, MUTED]), legend=None)
    else:
        color = alt.value(ACCENT)
    bars = base.mark_bar(size=18, cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        x=alt.X(f"{value}:Q", title=title, scale=alt.Scale(domain=[0, df[value].max() * 1.2])),
        color=color,
        tooltip=[alt.Tooltip(f"{name}:N", title="항목"), alt.Tooltip(f"{label}:N", title=title)],
    )
    texts = base.mark_text(align="left", dx=6, color=TEXT, fontSize=12).encode(x=f"{value}:Q", text=f"{label}:N")
    return _style((bars + texts).properties(height=max(120, 30 * len(df))))
