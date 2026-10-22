# 프로젝트: 얼마나 뛰지? — 다이어터 맞춤 운동 처방 서비스 (Streamlit)
대상: 저녁에 고칼로리 음식을 먹고 "얼마나 운동해야 하지?"가 막막한 다이어트 중인 대학생·직장인
## 구조
- app.py는 st.navigation으로 사이드바 메뉴(제목·아이콘·순서)만 정함. 화면은 screens/(0_홈, 1_뭐_먹었어, 2_이건_몇_칼로리), core.py 로직(streamlit import 금지), charts.py 차트(Altair), sources.py 출처 표시(화면마다 맨 아래에서 호출), widgets.py 숫자 입력 −/+ 버튼 부품, data/ CSV
- 화면 폴더 이름을 pages로 짓지 말 것 (Streamlit이 예전 방식으로 먼저 시작해 처음에 app만 보임)
- 화면 파일에서 st.set_page_config를 부르지 말 것 (app.py에서 한 번만)
- 데이터 로드는 @st.cache_data, 경로는 app.py 기준 상대 경로 (절대 경로 금지)
- 결과·이력은 st.session_state에 저장하고 버튼/폼 밖에서 표시
## 코딩 규칙
- Python 3, streamlit, pandas. 새 패키지는 설치하기 전에 먼저 물어볼 것 (설치하면 requirements.txt에도 추가)
- 함수에는 한글 docstring, 화면 문구는 한국어 존댓말
- 빈 입력·빈 검색 결과·범위 밖 값에서 오류 대신 st.warning (number_input에는 min·max·기본값)
- 열 이름은 data/README.md의 목록만 사용 (지어내지 말 것)
- 음식 검색은 str.contains 수준으로 단순하게. 못 찾으면 kcal 직접 입력으로 넘긴다
- 1단계 core.py는 규칙 기반(체중 × MET × 시간). 2단계에서 소모 칼로리 회귀 모델로 교체할 수 있게 반환 형식을 고정한다
## 하지 말 것
- 요청한 파일 외 수정, 전체 재작성, 비밀값 하드코딩
- 이 폴더(~/work/project/diet_app) 밖의 파일 접근, rm -rf / sudo 실행
- data/의 실제 데이터 파일 수정·삭제 (예시 파일은 사용자가 직접 지운다)
- try/except로 오류를 삼키는 수정
## 검증
- core.py나 화면 파일 수정 시 python -m pytest -q 를 실행해 결과를 알려 줄 것 (test_core.py 계산, test_app.py 화면)
- 화면 파일 수정 후에는 "streamlit run app.py 로 확인하라"고 알려 줄 것 (실행은 내가 한다)
- 작업 하나가 끝나면 커밋 메시지 앞에 US-N: 을 붙이자고 알려 줄 것
