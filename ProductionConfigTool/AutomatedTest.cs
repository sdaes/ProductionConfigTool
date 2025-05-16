using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Windows.Forms;

namespace ProductionTesterApp
{
    public class AutomatedTest
    {
        private SerialHandler serialHandler;
        private List<string> testSequence;
        
        /// <summary>
        /// 자동화 테스트 클래스 초기화
        /// </summary>
        /// <param name="serialHandler">시리얼 통신 핸들러</param>
        /// <param name="testSequence">실행할 테스트 시퀀스 목록 (null인 경우 기본 시퀀스 사용)</param>
        public AutomatedTest(SerialHandler serialHandler, List<string> testSequence = null)
        {
            this.serialHandler = serialHandler ?? throw new ArgumentNullException(nameof(serialHandler));
            
            // 기본 테스트 시퀀스 설정
            this.testSequence = testSequence ?? new List<string>
            {
                "터치", "도플러 센서", "IR", "콘센트 릴레이", 
                "조명 릴레이", "미터링", "LED", "부저"
            };
        }
        
        /// <summary>
        /// 자동화 테스트 시퀀스 실행
        /// </summary>
        /// <param name="progressCallback">진행 상황 콜백 함수 (현재 테스트 이름, 진행률)</param>
        /// <returns>테스트 결과 및 요약 정보를 담은 딕셔너리</returns>
        public Dictionary<string, object> RunAutomatedTestSequence(Action<string, int> progressCallback = null)
        {
            // 결과를 저장할 딕셔너리
            Dictionary<string, Dictionary<string, string>> results = new Dictionary<string, Dictionary<string, string>>();
            Dictionary<string, object> summary = new Dictionary<string, object>();
            
            summary["총 검사 수"] = testSequence.Count;
            summary["통과"] = 0;
            summary["실패"] = 0;
            summary["통과율"] = 0.0;
            summary["시작 시간"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            
            Stopwatch stopwatch = new Stopwatch();
            stopwatch.Start();
            
            // 테스트 시퀀스 실행
            for (int i = 0; i < testSequence.Count; i++)
            {
                string testType = testSequence[i];
                string testName = $"{testType} 검사";
                
                // 진행 상황 콜백
                progressCallback?.Invoke(testName, (i + 1) * 100 / testSequence.Count);
                
                // 테스트 실행
                try
                {
                    string result = TestFunctions.RunTest(testType, serialHandler);
                    
                    // 결과 저장
                    Dictionary<string, string> testResult = new Dictionary<string, string>();
                    testResult["결과"] = result;
                    testResult["시간"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                    results[testName] = testResult;
                    
                    // 요약 정보 업데이트
                    if (result == "통과")
                        summary["통과"] = Convert.ToInt32(summary["통과"]) + 1;
                    else
                        summary["실패"] = Convert.ToInt32(summary["실패"]) + 1;
                }
                catch (Exception ex)
                {
                    // 테스트 실패 처리
                    Dictionary<string, string> testResult = new Dictionary<string, string>();
                    testResult["결과"] = "실패";
                    testResult["시간"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                    testResult["오류"] = ex.Message;
                    results[testName] = testResult;
                    
                    summary["실패"] = Convert.ToInt32(summary["실패"]) + 1;
                }
            }
            
            // 테스트 완료 후 시간 정보 업데이트
            stopwatch.Stop();
            summary["종료 시간"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            summary["소요 시간"] = $"{stopwatch.ElapsedMilliseconds / 1000.0:F2}초";
            
            // 통과율 계산
            int totalTests = testSequence.Count;
            if (totalTests > 0)
            {
                summary["통과율"] = (Convert.ToDouble(summary["통과"]) / totalTests) * 100;
            }
            
            // 결과 반환
            Dictionary<string, object> finalResult = new Dictionary<string, object>();
            finalResult["results"] = results;
            finalResult["summary"] = summary;
            
            return finalResult;
        }
        
        /// <summary>
        /// 자동화 테스트 결과 표시
        /// </summary>
        /// <param name="testResults">테스트 결과 딕셔너리</param>
        /// <param name="parent">부모 컨트롤 (결과 표시용)</param>
        public static void DisplayAutomatedTestResults(Dictionary<string, object> testResults, Control parent = null)
        {
            if (testResults == null || !testResults.ContainsKey("results") || !testResults.ContainsKey("summary"))
            {
                MessageBox.Show("테스트 결과가 없습니다.", "결과 없음", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            
            // 요약 정보 추출
            Dictionary<string, object> summary = (Dictionary<string, object>)testResults["summary"];
            Dictionary<string, Dictionary<string, string>> results = (Dictionary<string, Dictionary<string, string>>)testResults["results"];
            
            // 결과 메시지 구성
            string resultMessage = "===== 자동화 테스트 결과 =====\n\n";
            
            resultMessage += $"총 검사 수: {summary["총 검사 수"]}\n";
            resultMessage += $"통과: {summary["통과"]}\n";
            resultMessage += $"실패: {summary["실패"]}\n";
            resultMessage += $"통과율: {summary["통과율"]:F2}%\n";
            resultMessage += $"시작 시간: {summary["시작 시간"]}\n";
            resultMessage += $"종료 시간: {summary["종료 시간"]}\n";
            resultMessage += $"소요 시간: {summary["소요 시간"]}\n\n";
            
            resultMessage += "===== 상세 검사 결과 =====\n\n";
            
            foreach (var entry in results)
            {
                string testName = entry.Key;
                Dictionary<string, string> testResult = entry.Value;
                
                resultMessage += $"테스트: {testName}\n";
                resultMessage += $"결과: {testResult["결과"]}\n";
                resultMessage += $"시간: {testResult["시간"]}\n";
                
                if (testResult.ContainsKey("오류"))
                    resultMessage += $"오류: {testResult["오류"]}\n";
                
                resultMessage += "\n";
            }
            
            // 실패한 테스트 목록
            int failCount = Convert.ToInt32(summary["실패"]);
            if (failCount > 0)
            {
                resultMessage += "===== 실패한 테스트 =====\n\n";
                
                foreach (var entry in results)
                {
                    if (entry.Value["결과"] == "실패")
                    {
                        resultMessage += $"- {entry.Key}\n";
                    }
                }
            }
            
            // 결과 표시
            MessageBox.Show(resultMessage, "자동화 테스트 결과", MessageBoxButtons.OK, 
                failCount == 0 ? MessageBoxIcon.Information : MessageBoxIcon.Warning);
        }
    }
}