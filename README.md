# 🏃 얼마나 뛰지? (다이어터 맞춤 운동 처방 서비스)

다이어트 중인 대학생·직장인을 위해, 신체 정보와 오늘 먹은 음식으로 필요한 운동 종류와 시간(분)을 알려 주는 서비스 (머신러닝프로젝트 1단계 프로토타입).
작성자: (공개용에서는 생략)

## 실행
```bash
cd ~/work/project/diet_app          # 항상 app.py가 있는 폴더에서
pip install -r requirements.txt     # 없는 것만 설치
streamlit run app.py                # 이 터미널은 앱 전용 — 닫지 않는다
```
브라우저: 터미널에 나오는 주소를 엽니다.
화면을 추가하면 screens/에 파일을 만들고 app.py의 `screens` 목록에도 등록한 뒤, Ctrl+C 후 다시 실행합니다.

## 구조
```
app.py             사이드바 메뉴(제목·아이콘·순서)만 정하는 진입 파일
screens/           화면: 0_홈 · 1_뭐_먹었어 · 2_이건_몇_칼로리
core.py            계산 로직 (streamlit import 금지)
charts.py          차트 (Altair)
sources.py         화면 끝의 데이터 출처·라이선스 표시
widgets.py         입력 칸 양옆에 항상 보이는 −/+ 버튼 부품
test_core.py       계산 함수 테스트
test_app.py        화면 동작 테스트 (python -m pytest -q 로 둘 다 실행)
data/              CSV (data/README.md에 열 목록·shape)
SPEC.md            기능 명세·진행표
CLAUDE.md          AI 규칙 파일
AI_LOG.md          AI 활용 기록
```

## 앱 주소
(내 앱 주소를 여기에 적기)

## 데이터
`data/README.md` 참고. 파일별 출처, shape, 열 목록, AI가 편집한 방법을 적어 두었습니다.

## 작업 규칙 5가지
1. 작업 하나 → 실행 확인 → 커밋
2. 커밋 메시지 앞에 `US-N:`
3. 되는 상태에서만 앱 재시작 (깨지면 `git restore <파일>`)
4. 패키지를 추가하면 `pip install`과 requirements.txt를 같은 커밋에
5. 비밀값은 코드에 쓰지 않는다 (`.streamlit/secrets.toml`, Git 제외)
