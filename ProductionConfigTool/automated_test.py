import streamlit as st
import pandas as pd
import numpy as np
import time
import datetime
from test_functions import run_test

def run_automated_test_sequence(serial_handler, test_sequence=None):
    """
    자동화된 테스트 시퀀스를 실행하는 함수
    
    Args:
        serial_handler: 시리얼 통신 핸들러
        test_sequence: 실행할 테스트 시퀀스 목록
        
    Returns:
        dict: 테스트 결과 딕셔너리
    """
    if test_sequence is None:
        test_sequence = [
            "터치", "도플러 센서", "IR", "콘센트 릴레이", 
            "조명 릴레이", "미터링", "LED", "부저"
        ]
    
    # 결과를 저장할 딕셔너리
    results = {}
    summary = {
        "총 검사 수": len(test_sequence),
        "통과": 0,
        "실패": 0,
        "통과율": 0.0,
        "시작 시간": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "종료 시간": "",
        "소요 시간": ""
    }
    
    start_time = time.time()
    
    # 테스트 시퀀스 실행
    for test_type in test_sequence:
        test_name = f"{test_type} 검사"
        st.info(f"{test_name} 실행 중...")
        
        # 테스트 실행
        try:
            result = run_test(test_type, serial_handler)
            
            # 결과 저장
            results[test_name] = {
                "결과": result,
                "시간": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 요약 정보 업데이트
            if result == "통과":
                summary["통과"] += 1
            else:
                summary["실패"] += 1
                
        except Exception as e:
            results[test_name] = {
                "결과": "실패",
                "시간": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "오류": str(e)
            }
            summary["실패"] += 1
    
    # 테스트 완료 후 시간 정보 업데이트
    end_time = time.time()
    summary["종료 시간"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary["소요 시간"] = f"{end_time - start_time:.2f}초"
    
    # 통과율 계산
    if summary["총 검사 수"] > 0:
        summary["통과율"] = (summary["통과"] / summary["총 검사 수"]) * 100
    
    return {
        "results": results,
        "summary": summary
    }

def display_automated_test_results(test_results):
    """
    자동화된 테스트 결과를 표시하는 함수
    
    Args:
        test_results: 테스트 결과 딕셔너리
    """
    if not test_results:
        st.warning("테스트 결과가 없습니다.")
        return
    
    # 요약 정보 표시
    summary = test_results["summary"]
    results = test_results["results"]
    
    # 요약 카드
    st.subheader("테스트 요약")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("총 검사 수", summary["총 검사 수"])
    with col2:
        st.metric("통과", summary["통과"])
    with col3: 
        st.metric("실패", summary["실패"])
    
    # 통과율 게이지
    st.subheader("검사 통과율")
    pass_rate = summary["통과율"]
    st.progress(pass_rate / 100)
    st.write(f"{pass_rate:.2f}% 통과")
    
    # 테스트 시간 정보
    st.subheader("검사 시간 정보")
    time_col1, time_col2, time_col3 = st.columns(3)
    with time_col1:
        st.write("시작 시간:", summary["시작 시간"])
    with time_col2:
        st.write("종료 시간:", summary["종료 시간"])
    with time_col3:
        st.write("소요 시간:", summary["소요 시간"])
    
    # 상세 테스트 결과 테이블
    st.subheader("상세 검사 결과")
    
    # 결과를 DataFrame으로 변환
    result_df = pd.DataFrame([
        {
            "테스트": test_name,
            "결과": data["결과"],
            "시간": data["시간"],
            "오류": data.get("오류", "-")
        }
        for test_name, data in results.items()
    ])
    
    # 테이블 스타일 함수
    def highlight_result(val):
        if val == "통과":
            return "background-color: #CCFFCC"
        elif val == "실패":
            return "background-color: #FFCCCC"
        return ""
    
    # 결과 테이블 표시
    st.dataframe(
        result_df.style.applymap(highlight_result, subset=['결과']),
        use_container_width=True
    )
    
    # 테스트 결과에 따른 메시지
    if summary["실패"] == 0:
        st.success("🎉 모든 테스트가 통과되었습니다!")
    else:
        failed_tests = [test for test, data in results.items() if data["결과"] == "실패"]
        st.error(f"⚠️ {len(failed_tests)}개의 테스트가 실패했습니다: {', '.join(failed_tests)}")

def automated_test_ui():
    """
    자동화된 테스트 UI 컴포넌트
    """
    st.header("자동화 검사 시퀀스")
    
    # 테스트 시퀀스 설정
    st.subheader("검사 시퀀스 설정")
    
    # 가능한 모든 테스트 목록
    all_tests = ["터치", "도플러 센서", "IR", "콘센트 릴레이", "조명 릴레이", "미터링", "LED", "부저"]
    
    # 테스트 시퀀스 선택
    selected_tests = st.multiselect(
        "실행할 검사 항목 선택",
        options=all_tests,
        default=st.session_state.test_sequence
    )
    
    # 선택된 테스트 시퀀스 저장
    if selected_tests:
        st.session_state.test_sequence = selected_tests
    
    # 테스트 순서 조정
    st.info("검사 순서를 변경하려면 위의 선택 항목에서 제거 후 원하는 순서로 다시 추가하세요.")
    
    # 테스트 실행 버튼
    if st.button("자동 검사 시퀀스 실행", 
                disabled=not st.session_state.serial_connected or len(selected_tests) == 0):
        
        # 테스트 결과를 저장할 공간 초기화
        st.session_state.auto_test_running = True
        
        # 테스트 실행
        with st.spinner("자동화 검사 시퀀스 실행 중입니다..."):
            test_results = run_automated_test_sequence(
                st.session_state.serial_handler, 
                st.session_state.test_sequence
            )
            
            # 테스트 결과 저장
            st.session_state.auto_test_results = test_results
            
            # 테스트 결과 업데이트
            for test_name, data in test_results["results"].items():
                # 테스트 이름에서 "검사" 제거
                test_type = test_name.replace(" 검사", "")
                
                # 제품 정보 가져오기
                product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
                current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
                
                # 테스트 결과를 전체 결과에 추가
                new_result = pd.DataFrame({
                    '테스트': [test_name],
                    '결과': [data["결과"]],
                    '시간': [data["시간"]],
                    '제품 종류': [current_product],
                    '조명 회로': [st.session_state.config_data['light_circuits']],
                    '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                    '디밍 종류': [st.session_state.config_data['dimming_type']]
                })
                st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
                
                # 테스트 통계 업데이트 - 테스트 통계 함수가 있는지 확인하고 호출
                update_test_statistics_fn = globals().get("update_test_statistics", None)
                if update_test_statistics_fn is None and hasattr(st.session_state, "update_test_statistics"):
                    update_test_statistics_fn = st.session_state.update_test_statistics
                
                if update_test_statistics_fn:
                    update_test_statistics_fn(test_name, data["결과"])
            
            st.session_state.auto_test_running = False
        
    # 테스트 결과 표시
    if 'auto_test_results' in st.session_state and st.session_state.auto_test_results:
        display_automated_test_results(st.session_state.auto_test_results)
        
        if st.button("테스트 결과 초기화"):
            st.session_state.auto_test_results = {}
            st.rerun()