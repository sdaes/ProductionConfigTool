using System;
using System.Threading;

namespace ProductionTesterApp
{
    public static class TestFunctions
    {
        /// <summary>
        /// 장치에서 특정 테스트 실행
        /// </summary>
        /// <param name="testType">실행할 테스트 유형</param>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>"통과" 또는 "실패" 결과 문자열</returns>
        public static string RunTest(string testType, SerialHandler serialHandler)
        {
            if (serialHandler == null)
                throw new ArgumentNullException(nameof(serialHandler), "시리얼 핸들러가 초기화되지 않았습니다.");

            switch (testType)
            {
                case "터치":
                    return TouchTest(serialHandler) ? "통과" : "실패";
                case "도플러 센서":
                    return DopplerSensorTest(serialHandler) ? "통과" : "실패";
                case "IR":
                    return IRTest(serialHandler) ? "통과" : "실패";
                case "콘센트 릴레이":
                    return OutletRelayTest(serialHandler) ? "통과" : "실패";
                case "조명 릴레이":
                    return LightRelayTest(serialHandler) ? "통과" : "실패";
                case "미터링":
                    return MeteringTest(serialHandler) ? "통과" : "실패";
                case "LED":
                    return LEDTest(serialHandler) ? "통과" : "실패";
                case "부저":
                    return BuzzerTest(serialHandler) ? "통과" : "실패";
                default:
                    throw new ArgumentException($"알 수 없는 테스트 유형: {testType}");
            }
        }

        /// <summary>
        /// 터치 테스트 실행
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>테스트 통과 시 true, 실패 시 false</returns>
        private static bool TouchTest(SerialHandler serialHandler)
        {
            // 터치 테스트 명령 전송 (0x10)
            byte[] response = serialHandler.SendCommand(0x10);
            
            if (response != null && response.Length > 0)
            {
                // 응답 코드 확인 (예: 0x01은 성공)
                return response[0] == 0x01;
            }
            
            return false;
        }

        /// <summary>
        /// 도플러 센서 테스트 실행
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>테스트 통과 시 true, 실패 시 false</returns>
        private static bool DopplerSensorTest(SerialHandler serialHandler)
        {
            // 도플러 센서 테스트 명령 전송 (0x11)
            byte[] response = serialHandler.SendCommand(0x11);
            
            if (response != null && response.Length > 0)
            {
                // 응답 코드 확인
                return response[0] == 0x01;
            }
            
            return false;
        }

        /// <summary>
        /// IR 테스트 실행
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>테스트 통과 시 true, 실패 시 false</returns>
        private static bool IRTest(SerialHandler serialHandler)
        {
            // IR 테스트 명령 전송 (0x12)
            byte[] response = serialHandler.SendCommand(0x12);
            
            if (response != null && response.Length > 0)
            {
                // 응답 코드 확인
                return response[0] == 0x01;
            }
            
            return false;
        }

        /// <summary>
        /// 콘센트 릴레이 테스트 실행
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>테스트 통과 시 true, 실패 시 false</returns>
        private static bool OutletRelayTest(SerialHandler serialHandler)
        {
            // 콘센트 릴레이 테스트 명령 전송 (0x13)
            byte[] response = serialHandler.SendCommand(0x13);
            
            if (response != null && response.Length > 0)
            {
                // 응답 코드 확인
                return response[0] == 0x01;
            }
            
            return false;
        }

        /// <summary>
        /// 조명 릴레이 테스트 실행
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>테스트 통과 시 true, 실패 시 false</returns>
        private static bool LightRelayTest(SerialHandler serialHandler)
        {
            // 조명 릴레이 테스트 명령 전송 (0x14)
            byte[] response = serialHandler.SendCommand(0x14);
            
            if (response != null && response.Length > 0)
            {
                // 응답 코드 확인
                return response[0] == 0x01;
            }
            
            return false;
        }

        /// <summary>
        /// 미터링 테스트 실행
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>테스트 통과 시 true, 실패 시 false</returns>
        private static bool MeteringTest(SerialHandler serialHandler)
        {
            // 미터링 테스트 명령 전송 (0x15)
            byte[] response = serialHandler.SendCommand(0x15);
            
            if (response != null && response.Length > 0)
            {
                // 응답의 길이가 충분한지 확인
                if (response.Length >= 3)
                {
                    // 응답 코드 확인 (예: 0x01은 성공)
                    if (response[0] == 0x01)
                    {
                        // 미터링 값이 유효 범위 내에 있는지 확인
                        int meterValue = (response[1] << 8) | response[2];
                        return meterValue > 0 && meterValue < 1000; // 예: 0-1000 범위 내
                    }
                }
            }
            
            return false;
        }

        /// <summary>
        /// LED 테스트 실행
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>테스트 통과 시 true, 실패 시 false</returns>
        private static bool LEDTest(SerialHandler serialHandler)
        {
            // LED 테스트 명령 전송 (0x16)
            byte[] response = serialHandler.SendCommand(0x16);
            
            if (response != null && response.Length > 0)
            {
                // 응답 코드 확인
                return response[0] == 0x01;
            }
            
            return false;
        }

        /// <summary>
        /// 부저 테스트 실행
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>테스트 통과 시 true, 실패 시 false</returns>
        private static bool BuzzerTest(SerialHandler serialHandler)
        {
            // 부저 테스트 명령 전송 (0x17)
            byte[] response = serialHandler.SendCommand(0x17);
            
            if (response != null && response.Length > 0)
            {
                // 응답 코드 확인
                return response[0] == 0x01;
            }
            
            return false;
        }

        /// <summary>
        /// 모든 테스트 순차적으로 실행
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <returns>테스트 결과를 담은 딕셔너리</returns>
        public static Dictionary<string, string> RunAllTests(SerialHandler serialHandler)
        {
            if (serialHandler == null)
                throw new ArgumentNullException(nameof(serialHandler), "시리얼 핸들러가 초기화되지 않았습니다.");

            string[] testTypes = {
                "터치", "도플러 센서", "IR", "콘센트 릴레이", 
                "조명 릴레이", "미터링", "LED", "부저"
            };

            Dictionary<string, string> results = new Dictionary<string, string>();

            foreach (string testType in testTypes)
            {
                try
                {
                    string result = RunTest(testType, serialHandler);
                    results.Add($"{testType} 검사", result);
                }
                catch (Exception ex)
                {
                    results.Add($"{testType} 검사", $"오류: {ex.Message}");
                }
                
                // 각 테스트 사이에 짧은 딜레이
                Thread.Sleep(100);
            }

            return results;
        }
    }
}