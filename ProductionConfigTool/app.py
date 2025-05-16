import streamlit as st
import serial.tools.list_ports
import pandas as pd
import numpy as np
import time
import datetime
import matplotlib.pyplot as plt
import io
from serial_handler import SerialHandler
from packet_builder import PacketBuilder
from test_functions import run_test
from utils import get_current_datetime_bytes
from automated_test import automated_test_ui

# Set page title and configuration
st.set_page_config(
    page_title="생산 제품 설정 및 검사 프로그램",
    page_icon="🔌",
    layout="wide",
)

st.title("스위치 생산 설정 및 검사 프로그램")

# Function to update test statistics
def update_test_statistics(test_name, result):
    """
    Update test statistics for the given test
    
    Args:
        test_name (str): Name of the test
        result (str): Result of the test ('통과' or '실패')
    """
    # Update test counts by type
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # If the test doesn't exist in the DataFrame, add it
    if not any(st.session_state.test_count_by_type['테스트'] == test_name):
        new_test = pd.DataFrame({
            '테스트': [test_name],
            '통과 수': [1 if result == '통과' else 0],
            '실패 수': [1 if result == '실패' else 0],
            '총 검사 수': [1],
            '통과율': [100.0 if result == '통과' else 0.0]
        })
        st.session_state.test_count_by_type = pd.concat([st.session_state.test_count_by_type, new_test], ignore_index=True)
    else:
        # Update existing test statistics
        test_idx = st.session_state.test_count_by_type[st.session_state.test_count_by_type['테스트'] == test_name].index[0]
        
        if result == '통과':
            st.session_state.test_count_by_type.at[test_idx, '통과 수'] += 1
        else:
            st.session_state.test_count_by_type.at[test_idx, '실패 수'] += 1
            
        st.session_state.test_count_by_type.at[test_idx, '총 검사 수'] += 1
        
        # Calculate pass rate
        pass_count = st.session_state.test_count_by_type.at[test_idx, '통과 수']
        total_count = st.session_state.test_count_by_type.at[test_idx, '총 검사 수']
        pass_rate = (pass_count / total_count) * 100 if total_count > 0 else 0
        st.session_state.test_count_by_type.at[test_idx, '통과율'] = pass_rate
    
    # Update daily pass rate
    if not any(st.session_state.daily_pass_rate['날짜'] == today):
        new_day = pd.DataFrame({
            '날짜': [today],
            '통과 수': [1 if result == '통과' else 0],
            '실패 수': [1 if result == '실패' else 0],
            '총 검사 수': [1],
            '통과율': [100.0 if result == '통과' else 0.0]
        })
        st.session_state.daily_pass_rate = pd.concat([st.session_state.daily_pass_rate, new_day], ignore_index=True)
    else:
        # Update existing day statistics
        day_idx = st.session_state.daily_pass_rate[st.session_state.daily_pass_rate['날짜'] == today].index[0]
        
        if result == '통과':
            st.session_state.daily_pass_rate.at[day_idx, '통과 수'] += 1
        else:
            st.session_state.daily_pass_rate.at[day_idx, '실패 수'] += 1
            
        st.session_state.daily_pass_rate.at[day_idx, '총 검사 수'] += 1
        
        # Calculate pass rate
        pass_count = st.session_state.daily_pass_rate.at[day_idx, '통과 수']
        total_count = st.session_state.daily_pass_rate.at[day_idx, '총 검사 수']
        pass_rate = (pass_count / total_count) * 100 if total_count > 0 else 0
        st.session_state.daily_pass_rate.at[day_idx, '통과율'] = pass_rate

# Initialize session state variables if they don't exist
if 'serial_connected' not in st.session_state:
    st.session_state.serial_connected = False
if 'serial_handler' not in st.session_state:
    st.session_state.serial_handler = None
if 'test_results' not in st.session_state:
    st.session_state.test_results = pd.DataFrame(columns=['테스트', '결과', '시간', '제품 종류', '조명 회로', '콘센트 회로', '디밍 종류'])
if 'daily_pass_rate' not in st.session_state:
    st.session_state.daily_pass_rate = pd.DataFrame(columns=['날짜', '통과 수', '실패 수', '총 검사 수', '통과율'])
if 'test_count_by_type' not in st.session_state:
    st.session_state.test_count_by_type = pd.DataFrame(columns=['테스트', '통과 수', '실패 수', '총 검사 수', '통과율'])
if 'auto_test_running' not in st.session_state:
    st.session_state.auto_test_running = False
if 'auto_test_results' not in st.session_state:
    st.session_state.auto_test_results = {}
if 'test_sequence' not in st.session_state:
    st.session_state.test_sequence = [
        "터치", "도플러 센서", "IR", "콘센트 릴레이", "조명 릴레이", "미터링", "LED", "부저"
    ]
# 테스트 통계 업데이트 함수 세션 상태에 저장
st.session_state.update_test_statistics = update_test_statistics
if 'config_data' not in st.session_state:
    st.session_state.config_data = {
        'product_type': 0x5B,  # Default: Light switch
        'mac_address': '0000',  # Default MAC address (last 2 bytes)
        'light_circuits': 1,     # 1-4 circuits
        'outlet_circuits': 0,    # 0-2 circuits
        'dimming_type': 0,       # 0: None, 1: Dimming, 2: Color temperature
        'delay_time': 0,         # 0-5 seconds
        'sub_id': 0,             # SUB ID
        'ir_present': 0,         # IR presence
        'scenario': 0,           # Scenario selection
        'comm_company': 0,       # Communication company
        'three_way': 0,          # 3-Way selection
        'overload_protection': 0, # 0: Sum, 1: Individual
        'emergency_call': 0,      # 0: None, 1: Present
        'outlet1_learn_value': 0, # Outlet 1 learn value
        'outlet1_current_value': 0, # Outlet 1 current value
        'outlet2_learn_value': 0,   # Outlet 2 learn value
        'outlet2_current_value': 0, # Outlet 2 current value
        'relay_status': 0,        # Relay ON/OFF status
        'outlet1_mode': 0,        # 0: Manual, 1: Auto
        'outlet2_mode': 0,        # 0: Manual, 1: Auto
        'sleep_mode': 0,          # 0: Not used, 1: Used
        'delay_mode': 0,          # 0: Not used, 1: Used
        'dimming_value': 0,       # Current dimming value
        'color_temp_value': 0,    # Current color temperature value
    }

# Serial Communication Setup
st.sidebar.header("통신 설정")

# Get available COM ports
ports = [port.device for port in serial.tools.list_ports.comports()]
selected_port = st.sidebar.selectbox("시리얼 포트 선택", ports)

if st.sidebar.button("연결" if not st.session_state.serial_connected else "연결 해제"):
    if not st.session_state.serial_connected:
        try:
            st.session_state.serial_handler = SerialHandler(selected_port, 115200)
            st.session_state.serial_connected = True
            st.sidebar.success(f"{selected_port}에 연결되었습니다.")
        except Exception as e:
            st.sidebar.error(f"연결 실패: {str(e)}")
    else:
        if st.session_state.serial_handler:
            st.session_state.serial_handler.close()
        st.session_state.serial_connected = False
        st.session_state.serial_handler = None
        st.sidebar.info("연결이 해제되었습니다.")

# Connection status indicator
st.sidebar.metric(
    "연결 상태", 
    "연결됨" if st.session_state.serial_connected else "연결 안됨",
    delta=None,
    delta_color="off"
)

# Main content with tabs
tab1, tab2, tab3 = st.tabs(["제품 설정", "검사 기능", "검사 데이터 분석"])

# Config Tab
with tab1:
    st.header("제품 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Product Type Selection
        product_type_options = {
            "조명 스위치": 0x5B,
            "콘센트 스위치": 0x5C,
            "디밍 스위치": 0x5D
        }
        selected_product = st.selectbox(
            "제품 종류",
            options=list(product_type_options.keys()),
            index=list(product_type_options.values()).index(st.session_state.config_data['product_type'])
        )
        st.session_state.config_data['product_type'] = product_type_options[selected_product]
        
        # MAC Address (last 2 bytes)
        mac_address = st.text_input(
            "디바이스 MAC 주소 (마지막 2바이트, HEX)",
            value=st.session_state.config_data['mac_address']
        )
        if len(mac_address) == 4 and all(c in '0123456789ABCDEFabcdef' for c in mac_address):
            st.session_state.config_data['mac_address'] = mac_address
            
        # Light Circuits
        st.session_state.config_data['light_circuits'] = st.number_input(
            "조명 회로 수 (1-4)",
            min_value=1,
            max_value=4,
            value=st.session_state.config_data['light_circuits']
        )
        
        # Outlet Circuits
        st.session_state.config_data['outlet_circuits'] = st.number_input(
            "콘센트 회로 수 (0-2)",
            min_value=0,
            max_value=2,
            value=st.session_state.config_data['outlet_circuits']
        )
        
        # Dimming Type
        dimming_options = {
            "없음": 0,
            "디밍": 1,
            "색온도": 2
        }
        selected_dimming = st.selectbox(
            "디밍 종류",
            options=list(dimming_options.keys()),
            index=st.session_state.config_data['dimming_type']
        )
        st.session_state.config_data['dimming_type'] = dimming_options[selected_dimming]
        
        # Delay Time
        st.session_state.config_data['delay_time'] = st.slider(
            "지연 시간 (초)",
            min_value=0,
            max_value=5,
            value=st.session_state.config_data['delay_time']
        )
        
        # Scenario selection
        scenario_options = ["하이어", "하이어2", "네오티마", "힐리즈", "LT 3.0", "LT 4.0", "SS패턴"]
        selected_scenario = st.selectbox(
            "시나리오",
            options=scenario_options,
            index=st.session_state.config_data['scenario']
        )
        st.session_state.config_data['scenario'] = scenario_options.index(selected_scenario)
        
    with col2:
        # Communication company
        comm_options = ["CVNET", "HT", "CMX", "KOCOM", "KDONE", "ZIGBANG", "HDCLABS"]
        selected_comm = st.selectbox(
            "통신사",
            options=comm_options,
            index=st.session_state.config_data['comm_company']
        )
        st.session_state.config_data['comm_company'] = comm_options.index(selected_comm)
        
        # SUB ID
        st.session_state.config_data['sub_id'] = st.number_input(
            "SUB ID",
            min_value=0,
            max_value=255,
            value=st.session_state.config_data['sub_id']
        )
        
        # IR presence
        st.session_state.config_data['ir_present'] = 1 if st.checkbox(
            "IR 있음",
            value=bool(st.session_state.config_data['ir_present'])
        ) else 0
        
        # 3-Way
        st.session_state.config_data['three_way'] = 1 if st.checkbox(
            "3Way 사용",
            value=bool(st.session_state.config_data['three_way'])
        ) else 0
        
        # Overload protection
        overload_options = {"합산": 0, "개별": 1}
        selected_overload = st.selectbox(
            "과부하 차단",
            options=list(overload_options.keys()),
            index=st.session_state.config_data['overload_protection']
        )
        st.session_state.config_data['overload_protection'] = overload_options[selected_overload]
        
        # Emergency call
        st.session_state.config_data['emergency_call'] = 1 if st.checkbox(
            "비상호출 기능",
            value=bool(st.session_state.config_data['emergency_call'])
        ) else 0
        
        # Sleep mode and delay mode
        st.session_state.config_data['sleep_mode'] = 1 if st.checkbox(
            "슬립모드 사용",
            value=bool(st.session_state.config_data['sleep_mode'])
        ) else 0
        
        st.session_state.config_data['delay_mode'] = 1 if st.checkbox(
            "지연모드 사용",
            value=bool(st.session_state.config_data['delay_mode'])
        ) else 0
    
    # Additional settings for outlet values and dimming if applicable
    # 콘센트 설정을 항상 표시
    st.subheader("콘센트 설정")
    
    out_col1, out_col2 = st.columns(2)
    
    with out_col1:
        st.markdown("### 콘센트 1")
        st.session_state.config_data['outlet1_learn_value'] = st.number_input(
            "콘센트 1 학습값",
            min_value=0,
            max_value=65535,
            value=st.session_state.config_data['outlet1_learn_value']
        )
        
        st.session_state.config_data['outlet1_current_value'] = st.number_input(
            "콘센트 1 현재값",
            min_value=0,
            max_value=65535,
            value=st.session_state.config_data['outlet1_current_value']
        )
        
        outlet1_mode_options = {"수동": 0, "자동": 1}
        selected_outlet1_mode = st.selectbox(
            "콘센트 1 설정모드",
            options=list(outlet1_mode_options.keys()),
            index=st.session_state.config_data['outlet1_mode']
        )
        st.session_state.config_data['outlet1_mode'] = outlet1_mode_options[selected_outlet1_mode]
    
    with out_col2:
        st.markdown("### 콘센트 2")
        st.session_state.config_data['outlet2_learn_value'] = st.number_input(
            "콘센트 2 학습값",
            min_value=0,
            max_value=65535,
            value=st.session_state.config_data['outlet2_learn_value']
        )
        
        st.session_state.config_data['outlet2_current_value'] = st.number_input(
            "콘센트 2 현재값",
            min_value=0,
            max_value=65535,
            value=st.session_state.config_data['outlet2_current_value']
        )
        
        outlet2_mode_options = {"수동": 0, "자동": 1}
        selected_outlet2_mode = st.selectbox(
            "콘센트 2 설정모드",
            options=list(outlet2_mode_options.keys()),
            index=st.session_state.config_data['outlet2_mode']
        )
        st.session_state.config_data['outlet2_mode'] = outlet2_mode_options[selected_outlet2_mode]
    
    # Settings for dimming if applicable
    if st.session_state.config_data['dimming_type'] > 0:
        st.subheader("디밍 설정")
        
        if st.session_state.config_data['dimming_type'] == 1:  # Dimming
            st.session_state.config_data['dimming_value'] = st.slider(
                "디밍 현재값",
                min_value=0,
                max_value=255,
                value=st.session_state.config_data['dimming_value']
            )
        
        elif st.session_state.config_data['dimming_type'] == 2:  # Color temperature
            st.session_state.config_data['color_temp_value'] = st.slider(
                "색온도 현재값",
                min_value=0,
                max_value=255,
                value=st.session_state.config_data['color_temp_value']
            )
    
    # Relay status
    st.subheader("릴레이 상태")
    relay_status = st.number_input(
        "릴레이 ON/OFF 상태 (비트로 표시)",
        min_value=0,
        max_value=255,
        value=st.session_state.config_data['relay_status']
    )
    st.session_state.config_data['relay_status'] = relay_status
    
    # Send configuration button
    if st.button("설정 전송", disabled=not st.session_state.serial_connected):
        try:
            # Create packet builder with current configuration
            packet_builder = PacketBuilder(st.session_state.config_data)
            packet = packet_builder.build_packet()
            
            # Send packet via serial
            st.session_state.serial_handler.send_packet(packet)
            
            # Display success message and packet details
            st.success("설정이 성공적으로 전송되었습니다.")
            
            # Display the packet in hex for debugging
            packet_hex = ' '.join([f"{b:02X}" for b in packet])
            st.code(f"전송된 패킷: {packet_hex}", language="")
            
        except Exception as e:
            st.error(f"전송 실패: {str(e)}")

# Testing Tab
with tab2:
    st.header("제품 검사")
    
    # Create tabs for manual and automated testing
    test_tab1, test_tab2 = st.tabs(["개별 검사", "자동화 검사 시퀀스"])
    
    # Manual Testing Tab
    with test_tab1:
        # Create three columns for test buttons
        test_col1, test_col2, test_col3 = st.columns(3)
        
        # Define test functions
        with test_col1:
            if st.button("터치 검사", disabled=not st.session_state.serial_connected):
                result = run_test("터치", st.session_state.serial_handler)
                
                # Get current product information
                product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
                current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
                
                # Add test result with more details
                new_result = pd.DataFrame({
                    '테스트': ['터치 검사'],
                    '결과': [result],
                    '시간': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    '제품 종류': [current_product],
                    '조명 회로': [st.session_state.config_data['light_circuits']],
                    '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                    '디밍 종류': [st.session_state.config_data['dimming_type']]
                })
                
                # 테스트 결과 업데이트
                st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
                
                # 테스트 통계 업데이트
                update_test_statistics("터치 검사", result)
            
        if st.button("IR 검사", disabled=not st.session_state.serial_connected):
            result = run_test("IR", st.session_state.serial_handler)
            
            # Get current product information
            product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
            current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
            
            # Add test result with more details
            new_result = pd.DataFrame({
                '테스트': ['IR 검사'],
                '결과': [result],
                '시간': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                '제품 종류': [current_product],
                '조명 회로': [st.session_state.config_data['light_circuits']],
                '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                '디밍 종류': [st.session_state.config_data['dimming_type']]
            })
            st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
            
            # Update test statistics
            update_test_statistics("IR 검사", result)
            
        if st.button("LED 검사", disabled=not st.session_state.serial_connected):
            result = run_test("LED", st.session_state.serial_handler)
            
            # Get current product information
            product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
            current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
            
            # Add test result with more details
            new_result = pd.DataFrame({
                '테스트': ['LED 검사'],
                '결과': [result],
                '시간': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                '제품 종류': [current_product],
                '조명 회로': [st.session_state.config_data['light_circuits']],
                '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                '디밍 종류': [st.session_state.config_data['dimming_type']]
            })
            st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
            
            # Update test statistics
            update_test_statistics("LED 검사", result)
    
    with test_col2:
        if st.button("도플러 센서 검사", disabled=not st.session_state.serial_connected):
            result = run_test("도플러 센서", st.session_state.serial_handler)
            
            # Get current product information
            product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
            current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
            
            # Add test result with more details
            new_result = pd.DataFrame({
                '테스트': ['도플러 센서 검사'],
                '결과': [result],
                '시간': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                '제품 종류': [current_product],
                '조명 회로': [st.session_state.config_data['light_circuits']],
                '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                '디밍 종류': [st.session_state.config_data['dimming_type']]
            })
            st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
            
            # Update test statistics
            update_test_statistics("도플러 센서 검사", result)
            
        if st.button("콘센트 릴레이 검사", disabled=not st.session_state.serial_connected):
            result = run_test("콘센트 릴레이", st.session_state.serial_handler)
            
            # Get current product information
            product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
            current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
            
            # Add test result with more details
            new_result = pd.DataFrame({
                '테스트': ['콘센트 릴레이 검사'],
                '결과': [result],
                '시간': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                '제품 종류': [current_product],
                '조명 회로': [st.session_state.config_data['light_circuits']],
                '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                '디밍 종류': [st.session_state.config_data['dimming_type']]
            })
            st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
            
            # Update test statistics
            update_test_statistics("콘센트 릴레이 검사", result)
            
        if st.button("부저 검사", disabled=not st.session_state.serial_connected):
            result = run_test("부저", st.session_state.serial_handler)
            
            # Get current product information
            product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
            current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
            
            # Add test result with more details
            new_result = pd.DataFrame({
                '테스트': ['부저 검사'],
                '결과': [result],
                '시간': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                '제품 종류': [current_product],
                '조명 회로': [st.session_state.config_data['light_circuits']],
                '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                '디밍 종류': [st.session_state.config_data['dimming_type']]
            })
            st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
            
            # Update test statistics
            update_test_statistics("부저 검사", result)
    
    with test_col3:
        if st.button("조명 릴레이 검사", disabled=not st.session_state.serial_connected):
            result = run_test("조명 릴레이", st.session_state.serial_handler)
            
            # Get current product information
            product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
            current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
            
            # Add test result with more details
            new_result = pd.DataFrame({
                '테스트': ['조명 릴레이 검사'],
                '결과': [result],
                '시간': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                '제품 종류': [current_product],
                '조명 회로': [st.session_state.config_data['light_circuits']],
                '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                '디밍 종류': [st.session_state.config_data['dimming_type']]
            })
            st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
            
            # Update test statistics
            update_test_statistics("조명 릴레이 검사", result)
            
        if st.button("미터링 검사", disabled=not st.session_state.serial_connected):
            result = run_test("미터링", st.session_state.serial_handler)
            
            # Get current product information
            product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
            current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
            
            # Add test result with more details
            new_result = pd.DataFrame({
                '테스트': ['미터링 검사'],
                '결과': [result],
                '시간': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                '제품 종류': [current_product],
                '조명 회로': [st.session_state.config_data['light_circuits']],
                '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                '디밍 종류': [st.session_state.config_data['dimming_type']]
            })
            st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
            
            # Update test statistics
            update_test_statistics("미터링 검사", result)
    
    # Run all tests
    if st.button("모든 검사 실행", disabled=not st.session_state.serial_connected):
        test_types = ["터치", "도플러 센서", "IR", "콘센트 릴레이", "조명 릴레이", "미터링", "LED", "부저"]
        
        # Get current product information
        product_types = {0x5B: "조명 스위치", 0x5C: "콘센트 스위치", 0x5D: "디밍 스위치"}
        current_product = product_types.get(st.session_state.config_data['product_type'], "알 수 없음")
        
        for test_type in test_types:
            result = run_test(test_type, st.session_state.serial_handler)
            
            # Add more detailed information for historical analysis
            new_result = pd.DataFrame({
                '테스트': [f"{test_type} 검사"],
                '결과': [result],
                '시간': [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                '제품 종류': [current_product],
                '조명 회로': [st.session_state.config_data['light_circuits']],
                '콘센트 회로': [st.session_state.config_data['outlet_circuits']],
                '디밍 종류': [st.session_state.config_data['dimming_type']]
            })
            st.session_state.test_results = pd.concat([st.session_state.test_results, new_result], ignore_index=True)
            
            # Update test statistics
            update_test_statistics(f"{test_type} 검사", result)
    
    # 자동화 테스트 탭
    with test_tab2:
        automated_test_ui()
    
    # Show test results
    st.subheader("검사 결과")
    
    # Style the dataframe to highlight pass/fail
    def highlight_result(val):
        if val == "통과":
            return "background-color: #CCFFCC"
        elif val == "실패":
            return "background-color: #FFCCCC"
        return ""
    
    # Display the test results
    if not st.session_state.test_results.empty:
        st.dataframe(
            st.session_state.test_results.style.applymap(highlight_result, subset=['결과']),
            use_container_width=True
        )
        
        # Add button to clear results
        if st.button("결과 초기화"):
            st.session_state.test_results = pd.DataFrame(columns=['테스트', '결과', '시간'])
            st.rerun()
    else:
        st.info("검사 결과가 없습니다. 검사를 실행하세요.")

# Analysis Tab
with tab3:
    st.header("검사 데이터 분석")
    
    # Create tabs for different analysis views
    analysis_tab1, analysis_tab2, analysis_tab3, analysis_tab4 = st.tabs([
        "일별 통계", "검사 유형별 통계", "제품 유형별 통계", "실패율 분석"
    ])
    
    # Function to generate charts
    def generate_chart(data, x_col, y_col, title, kind='bar', color=None):
        """Generate a matplotlib chart and return it as a Streamlit figure"""
        fig, ax = plt.subplots(figsize=(10, 5))
        
        if kind == 'bar':
            if color:
                data.plot(kind=kind, x=x_col, y=y_col, ax=ax, color=color, rot=45)
            else:
                data.plot(kind=kind, x=x_col, y=y_col, ax=ax, rot=45)
        elif kind == 'pie':
            # For pie charts, we need to handle data differently
            data[y_col].plot(kind=kind, ax=ax, autopct='%1.1f%%')
            ax.set_ylabel('')
        
        ax.set_title(title)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert plot to a Streamlit-compatible format
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Close the plot to prevent memory leaks
        plt.close(fig)
        
        return buf
    
    # Daily statistics tab
    with analysis_tab1:
        st.subheader("일별 검사 통계")
        
        if st.session_state.daily_pass_rate.empty:
            st.info("검사 데이터가 없습니다. 검사를 실행하여 데이터를 수집하세요.")
        else:
            # Sort by date
            daily_data = st.session_state.daily_pass_rate.sort_values(by='날짜')
            
            # Create two columns for charts
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Daily test counts
                pass_fail_data = daily_data[['날짜', '통과 수', '실패 수']]
                pass_fail_chart = generate_chart(
                    pass_fail_data, 
                    '날짜', 
                    ['통과 수', '실패 수'], 
                    '일별 검사 결과',
                    color=['green', 'red']
                )
                st.image(pass_fail_chart)
            
            with chart_col2:
                # Daily pass rate
                pass_rate_chart = generate_chart(
                    daily_data,
                    '날짜',
                    '통과율',
                    '일별 검사 통과율 (%)',
                    color='blue'
                )
                st.image(pass_rate_chart)
            
            # Display the data table
            st.subheader("일별 검사 데이터")
            st.dataframe(daily_data, use_container_width=True)
    
    # Test type statistics tab
    with analysis_tab2:
        st.subheader("검사 유형별 통계")
        
        if st.session_state.test_count_by_type.empty:
            st.info("검사 데이터가 없습니다. 검사를 실행하여 데이터를 수집하세요.")
        else:
            # Create two columns for charts
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Pass/fail by test type
                test_data = st.session_state.test_count_by_type[['테스트', '통과 수', '실패 수']]
                test_chart = generate_chart(
                    test_data,
                    '테스트',
                    ['통과 수', '실패 수'],
                    '검사 유형별 결과',
                    color=['green', 'red']
                )
                st.image(test_chart)
            
            with chart_col2:
                # Pass rate by test type
                pass_rate_chart = generate_chart(
                    st.session_state.test_count_by_type,
                    '테스트',
                    '통과율',
                    '검사 유형별 통과율 (%)',
                    color='blue'
                )
                st.image(pass_rate_chart)
            
            # Display the data table
            st.subheader("검사 유형별 데이터")
            st.dataframe(st.session_state.test_count_by_type, use_container_width=True)
    
    # Product type statistics tab
    with analysis_tab3:
        st.subheader("제품 유형별 통계")
        
        if st.session_state.test_results.empty:
            st.info("검사 데이터가 없습니다. 검사를 실행하여 데이터를 수집하세요.")
        else:
            # Group by product type and calculate statistics
            product_stats = st.session_state.test_results.groupby('제품 종류').agg(
                통과=('결과', lambda x: (x == '통과').sum()),
                실패=('결과', lambda x: (x == '실패').sum()),
                총검사수=('결과', 'count')
            ).reset_index()
            
            # Calculate pass rate
            product_stats['통과율'] = (product_stats['통과'] / product_stats['총검사수'] * 100).round(2)
            
            # Create charts
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Tests by product type
                product_chart = generate_chart(
                    product_stats,
                    '제품 종류',
                    ['통과', '실패'],
                    '제품 유형별 검사 결과',
                    color=['green', 'red']
                )
                st.image(product_chart)
            
            with chart_col2:
                # Distribution of tests by product type as pie chart
                test_distribution = generate_chart(
                    product_stats,
                    None,
                    '총검사수',
                    '제품 유형별 검사 분포',
                    kind='pie'
                )
                st.image(test_distribution)
            
            # Display the data table
            st.subheader("제품 유형별 데이터")
            st.dataframe(product_stats, use_container_width=True)
    
    # Failure analysis tab
    with analysis_tab4:
        st.subheader("실패율 분석")
        
        if st.session_state.test_results.empty:
            st.info("검사 데이터가 없습니다. 검사를 실행하여 데이터를 수집하세요.")
        else:
            # Filter the data to only include failed tests
            failed_tests = st.session_state.test_results[st.session_state.test_results['결과'] == '실패']
            
            if failed_tests.empty:
                st.success("모든 검사가 통과되었습니다! 실패한 검사가 없습니다.")
            else:
                # Group by test type and count failures
                failure_counts_by_test = failed_tests.groupby('테스트').size()
                failure_by_test = pd.DataFrame({
                    '테스트': failure_counts_by_test.index,
                    '실패 수': failure_counts_by_test.values
                })
                failure_by_test = failure_by_test.sort_values('실패 수', ascending=False)
                
                # Group by product type and count failures
                failure_counts_by_product = failed_tests.groupby('제품 종류').size()
                failure_by_product = pd.DataFrame({
                    '제품 종류': failure_counts_by_product.index,
                    '실패 수': failure_counts_by_product.values
                })
                failure_by_product = failure_by_product.sort_values('실패 수', ascending=False)
                
                # Create two columns for charts
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    # Failures by test type
                    test_failure_chart = generate_chart(
                        failure_by_test,
                        '테스트',
                        '실패 수',
                        '검사 유형별 실패 빈도',
                        color='red'
                    )
                    st.image(test_failure_chart)
                
                with chart_col2:
                    # Failures by product type
                    product_failure_chart = generate_chart(
                        failure_by_product,
                        '제품 종류',
                        '실패 수',
                        '제품 유형별 실패 빈도',
                        color='red'
                    )
                    st.image(product_failure_chart)
                
                # Show detailed failure data
                st.subheader("실패한 검사 세부 데이터")
                st.dataframe(failed_tests, use_container_width=True)

    # Display a button to export historical data 
    st.subheader("검사 데이터 내보내기")
    
    export_col1, export_col2 = st.columns(2)
    
    with export_col1:
        if st.button("CSV 파일로 내보내기"):
            if not st.session_state.test_results.empty:
                # Convert DataFrame to CSV
                csv = st.session_state.test_results.to_csv(index=False)
                
                # Create a download button
                st.download_button(
                    label="CSV 다운로드",
                    data=csv,
                    file_name="테스트_결과.csv",
                    mime="text/csv"
                )
            else:
                st.warning("내보낼 검사 데이터가 없습니다.")
    
    with export_col2:
        if st.button("데이터 초기화"):
            # Create a confirmation button
            confirm = st.checkbox("정말로 모든 검사 데이터를 초기화하시겠습니까?")
            
            if confirm:
                # Reset all test data
                st.session_state.test_results = pd.DataFrame(columns=['테스트', '결과', '시간', '제품 종류', '조명 회로', '콘센트 회로', '디밍 종류'])
                st.session_state.daily_pass_rate = pd.DataFrame(columns=['날짜', '통과 수', '실패 수', '총 검사 수', '통과율'])
                st.session_state.test_count_by_type = pd.DataFrame(columns=['테스트', '통과 수', '실패 수', '총 검사 수', '통과율'])
                st.success("모든 검사 데이터가 초기화되었습니다.")
                st.rerun()

# Display a footer with version information
st.markdown("---")
st.markdown("<div style='text-align: center;'>스위치 생산 설정 및 검사 프로그램 v1.0.0</div>", unsafe_allow_html=True)
