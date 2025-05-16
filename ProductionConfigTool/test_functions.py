import time
import random
import streamlit as st

def run_test(test_type, serial_handler):
    """
    Run a specific test on the device
    
    Args:
        test_type (str): Type of test to run
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        str: "통과" if test passed, "실패" if failed
    """
    if not serial_handler:
        st.error("시리얼 연결이 필요합니다.")
        return "실패"
    
    try:
        # Command codes for different test types
        test_commands = {
            "터치": 0x10,
            "도플러 센서": 0x11,
            "IR": 0x12,
            "콘센트 릴레이": 0x13,
            "조명 릴레이": 0x14,
            "미터링": 0x15,
            "LED": 0x16,
            "부저": 0x17
        }
        
        if test_type not in test_commands:
            st.error(f"알 수 없는 테스트 유형: {test_type}")
            return "실패"
        
        # Show test is running
        with st.spinner(f"{test_type} 검사 실행 중..."):
            # Send test command
            command_code = test_commands[test_type]
            response = serial_handler.send_command(command_code)
            
            # Process the response
            if response and len(response) >= 3:
                if response[0] == 0xDA and response[-1] == 0x25:
                    # Check the result code (assuming it's in the 3rd byte)
                    result_code = response[2]
                    
                    if result_code == 0:
                        return "통과"
                    else:
                        st.error(f"{test_type} 검사 실패: 오류 코드 {result_code}")
                        return "실패"
            
            st.error(f"{test_type} 검사 실패: 응답 없음 또는 잘못된 응답")
            return "실패"
    
    except Exception as e:
        st.error(f"{test_type} 검사 오류: {str(e)}")
        return "실패"

def touch_test(serial_handler):
    """
    Run touch test
    
    Args:
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        bool: True if test passed, False if failed
    """
    return run_test("터치", serial_handler) == "통과"

def doppler_sensor_test(serial_handler):
    """
    Run doppler sensor test
    
    Args:
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        bool: True if test passed, False if failed
    """
    return run_test("도플러 센서", serial_handler) == "통과"

def ir_test(serial_handler):
    """
    Run IR test
    
    Args:
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        bool: True if test passed, False if failed
    """
    return run_test("IR", serial_handler) == "통과"

def outlet_relay_test(serial_handler):
    """
    Run outlet relay test
    
    Args:
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        bool: True if test passed, False if failed
    """
    return run_test("콘센트 릴레이", serial_handler) == "통과"

def light_relay_test(serial_handler):
    """
    Run light relay test
    
    Args:
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        bool: True if test passed, False if failed
    """
    return run_test("조명 릴레이", serial_handler) == "통과"

def metering_test(serial_handler):
    """
    Run metering test
    
    Args:
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        bool: True if test passed, False if failed
    """
    return run_test("미터링", serial_handler) == "통과"

def led_test(serial_handler):
    """
    Run LED test
    
    Args:
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        bool: True if test passed, False if failed
    """
    return run_test("LED", serial_handler) == "통과"

def buzzer_test(serial_handler):
    """
    Run buzzer test
    
    Args:
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        bool: True if test passed, False if failed
    """
    return run_test("부저", serial_handler) == "통과"

def run_all_tests(serial_handler):
    """
    Run all tests sequentially
    
    Args:
        serial_handler (SerialHandler): Serial connection handler
        
    Returns:
        dict: Dictionary with test results
    """
    results = {}
    
    test_functions = [
        touch_test,
        doppler_sensor_test,
        ir_test,
        outlet_relay_test,
        light_relay_test,
        metering_test,
        led_test,
        buzzer_test
    ]
    
    for test_func in test_functions:
        test_name = test_func.__name__.replace("_test", "").replace("_", " ")
        results[test_name] = test_func(serial_handler)
    
    return results
