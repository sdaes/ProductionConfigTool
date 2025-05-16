using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.IO;
using System.IO.Ports;
using System.Linq;
using System.Text;
using System.Windows.Forms;

namespace ProductionTesterApp
{
    public partial class MainForm : Form
    {
        private SerialHandler serialHandler;
        private bool serialConnected = false;
        private Dictionary<string, object> configData;
        private DataTable testResults;
        private DataTable dailyPassRate;
        private DataTable testCountByType;

        public MainForm()
        {
            InitializeComponent();
            InitializeConfigData();
            InitializeDataTables();
        }

        private void InitializeConfigData()
        {
            // 설정 데이터 초기화
            configData = new Dictionary<string, object>
            {
                { "product_type", 0x5B }, // 기본값: Light switch
                { "mac_address", "0000" }, // 기본 MAC 주소 (마지막 2바이트)
                { "light_circuits", 1 }, // 조명 회로 수
                { "outlet_circuits", 1 }, // 콘센트 회로 수
                { "dimming_type", 0 } // 디밍 타입 (0: 없음)
            };
        }

        private void InitializeDataTables()
        {
            // 테스트 결과 데이터 테이블 초기화
            testResults = new DataTable();
            testResults.Columns.Add("테스트", typeof(string));
            testResults.Columns.Add("결과", typeof(string));
            testResults.Columns.Add("시간", typeof(string));
            testResults.Columns.Add("제품 종류", typeof(string));
            testResults.Columns.Add("조명 회로", typeof(int));
            testResults.Columns.Add("콘센트 회로", typeof(int));
            testResults.Columns.Add("디밍 종류", typeof(int));

            // 일별 통과율 데이터 테이블 초기화
            dailyPassRate = new DataTable();
            dailyPassRate.Columns.Add("날짜", typeof(string));
            dailyPassRate.Columns.Add("통과 수", typeof(int));
            dailyPassRate.Columns.Add("실패 수", typeof(int));
            dailyPassRate.Columns.Add("총 검사 수", typeof(int));
            dailyPassRate.Columns.Add("통과율", typeof(double));

            // 테스트 유형별 카운트 데이터 테이블 초기화
            testCountByType = new DataTable();
            testCountByType.Columns.Add("테스트", typeof(string));
            testCountByType.Columns.Add("통과 수", typeof(int));
            testCountByType.Columns.Add("실패 수", typeof(int));
            testCountByType.Columns.Add("총 검사 수", typeof(int));
            testCountByType.Columns.Add("통과율", typeof(double));
        }

        private void MainForm_Load(object sender, EventArgs e)
        {
            // 폼 로드 시 UI 초기화
            RefreshSerialPorts();
            UpdateConnectionStatus();
            tabControl.SelectedIndex = 0; // 첫 번째 탭 선택
        }

        private void RefreshSerialPorts()
        {
            // 시리얼 포트 목록 갱신
            cmbPorts.Items.Clear();
            foreach (string port in SerialPort.GetPortNames())
            {
                cmbPorts.Items.Add(port);
            }
            if (cmbPorts.Items.Count > 0)
                cmbPorts.SelectedIndex = 0;
        }

        private void btnRefreshPorts_Click(object sender, EventArgs e)
        {
            RefreshSerialPorts();
        }

        private void btnConnect_Click(object sender, EventArgs e)
        {
            if (!serialConnected)
            {
                // 연결
                try
                {
                    string selectedPort = cmbPorts.SelectedItem.ToString();
                    serialHandler = new SerialHandler(selectedPort, 115200);
                    serialConnected = true;
                    UpdateConnectionStatus();
                    MessageBox.Show("연결되었습니다.", "연결 성공", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"연결 실패: {ex.Message}", "연결 오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            else
            {
                // 연결 해제
                try
                {
                    serialHandler.Close();
                    serialConnected = false;
                    UpdateConnectionStatus();
                    MessageBox.Show("연결이 해제되었습니다.", "연결 해제", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"연결 해제 실패: {ex.Message}", "연결 해제 오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void UpdateConnectionStatus()
        {
            if (serialConnected)
            {
                btnConnect.Text = "연결 해제";
                lblConnectionStatus.Text = "연결됨";
                lblConnectionStatus.ForeColor = Color.Green;
            }
            else
            {
                btnConnect.Text = "연결";
                lblConnectionStatus.Text = "연결 안됨";
                lblConnectionStatus.ForeColor = Color.Red;
            }

            // 테스트 버튼 활성화/비활성화
            btnTouchTest.Enabled = serialConnected;
            btnIRTest.Enabled = serialConnected;
            btnDopplerTest.Enabled = serialConnected;
            btnOutletRelayTest.Enabled = serialConnected;
            btnLightRelayTest.Enabled = serialConnected;
            btnMeteringTest.Enabled = serialConnected;
            btnLEDTest.Enabled = serialConnected;
            btnBuzzerTest.Enabled = serialConnected;
            btnRunAutoTest.Enabled = serialConnected;

            // 설정 전송 버튼 활성화/비활성화
            btnSendConfig.Enabled = serialConnected;
        }

        private void btnSendConfig_Click(object sender, EventArgs e)
        {
            if (!serialConnected)
            {
                MessageBox.Show("먼저 장치에 연결하세요.", "연결 필요", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            try
            {
                // 설정값 가져오기
                byte productType = Convert.ToByte(configData["product_type"]);
                string macAddress = configData["mac_address"].ToString();
                int lightCircuits = Convert.ToInt32(configData["light_circuits"]);
                int outletCircuits = Convert.ToInt32(configData["outlet_circuits"]);
                int dimmingType = Convert.ToInt32(configData["dimming_type"]);

                // 패킷 빌더 생성
                PacketBuilder packetBuilder = new PacketBuilder(configData);
                byte[] packet = packetBuilder.BuildPacket();

                // 패킷 전송
                bool success = serialHandler.SendPacket(packet);

                if (success)
                {
                    MessageBox.Show("설정이 성공적으로 전송되었습니다.", "설정 전송", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                else
                {
                    MessageBox.Show("설정 전송에 실패했습니다.", "설정 전송 오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"설정 전송 중 오류 발생: {ex.Message}", "설정 전송 오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void btnTouchTest_Click(object sender, EventArgs e)
        {
            RunTest("터치");
        }

        private void btnIRTest_Click(object sender, EventArgs e)
        {
            RunTest("IR");
        }

        private void btnDopplerTest_Click(object sender, EventArgs e)
        {
            RunTest("도플러 센서");
        }

        private void btnOutletRelayTest_Click(object sender, EventArgs e)
        {
            RunTest("콘센트 릴레이");
        }

        private void btnLightRelayTest_Click(object sender, EventArgs e)
        {
            RunTest("조명 릴레이");
        }

        private void btnMeteringTest_Click(object sender, EventArgs e)
        {
            RunTest("미터링");
        }

        private void btnLEDTest_Click(object sender, EventArgs e)
        {
            RunTest("LED");
        }

        private void btnBuzzerTest_Click(object sender, EventArgs e)
        {
            RunTest("부저");
        }

        private void RunTest(string testType)
        {
            if (!serialConnected)
            {
                MessageBox.Show("먼저 장치에 연결하세요.", "연결 필요", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            try
            {
                Cursor = Cursors.WaitCursor;
                string result = TestFunctions.RunTest(testType, serialHandler);

                // 제품 정보 가져오기
                Dictionary<byte, string> productTypes = new Dictionary<byte, string>
                {
                    { 0x5B, "조명 스위치" },
                    { 0x5C, "콘센트 스위치" },
                    { 0x5D, "디밍 스위치" }
                };

                byte prodType = Convert.ToByte(configData["product_type"]);
                string currentProduct = productTypes.ContainsKey(prodType) ? productTypes[prodType] : "알 수 없음";

                // 테스트 결과 추가
                DataRow row = testResults.NewRow();
                row["테스트"] = testType + " 검사";
                row["결과"] = result;
                row["시간"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                row["제품 종류"] = currentProduct;
                row["조명 회로"] = configData["light_circuits"];
                row["콘센트 회로"] = configData["outlet_circuits"];
                row["디밍 종류"] = configData["dimming_type"];
                testResults.Rows.Add(row);

                // 테스트 통계 업데이트
                UpdateTestStatistics(testType + " 검사", result);

                // 데이터 그리드 업데이트
                dgvTestResults.DataSource = testResults;

                // 결과 표시
                MessageBox.Show($"테스트 결과: {result}", $"{testType} 검사 결과", MessageBoxButtons.OK, 
                    result == "통과" ? MessageBoxIcon.Information : MessageBoxIcon.Warning);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"테스트 실행 중 오류 발생: {ex.Message}", "테스트 오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                Cursor = Cursors.Default;
            }
        }

        private void UpdateTestStatistics(string testName, string result)
        {
            // 테스트 유형별 통계 업데이트
            DataRow[] rows = testCountByType.Select($"테스트 = '{testName}'");
            DataRow row;

            if (rows.Length == 0)
            {
                // 새 행 추가
                row = testCountByType.NewRow();
                row["테스트"] = testName;
                row["통과 수"] = 0;
                row["실패 수"] = 0;
                row["총 검사 수"] = 0;
                row["통과율"] = 0.0;
                testCountByType.Rows.Add(row);
            }
            else
            {
                row = rows[0];
            }

            // 결과에 따라 카운트 증가
            if (result == "통과")
                row["통과 수"] = Convert.ToInt32(row["통과 수"]) + 1;
            else
                row["실패 수"] = Convert.ToInt32(row["실패 수"]) + 1;

            row["총 검사 수"] = Convert.ToInt32(row["통과 수"]) + Convert.ToInt32(row["실패 수"]);
            double passRate = Convert.ToInt32(row["총 검사 수"]) > 0 ? 
                (Convert.ToDouble(row["통과 수"]) / Convert.ToInt32(row["총 검사 수"])) * 100 : 0;
            row["통과율"] = Math.Round(passRate, 2);
            
            // 일별 통계 업데이트
            string today = DateTime.Now.ToString("yyyy-MM-dd");
            DataRow[] dailyRows = dailyPassRate.Select($"날짜 = '{today}'");
            DataRow dailyRow;

            if (dailyRows.Length == 0)
            {
                // 새 행 추가
                dailyRow = dailyPassRate.NewRow();
                dailyRow["날짜"] = today;
                dailyRow["통과 수"] = 0;
                dailyRow["실패 수"] = 0;
                dailyRow["총 검사 수"] = 0;
                dailyRow["통과율"] = 0.0;
                dailyPassRate.Rows.Add(dailyRow);
            }
            else
            {
                dailyRow = dailyRows[0];
            }

            // 결과에 따라 카운트 증가
            if (result == "통과")
                dailyRow["통과 수"] = Convert.ToInt32(dailyRow["통과 수"]) + 1;
            else
                dailyRow["실패 수"] = Convert.ToInt32(dailyRow["실패 수"]) + 1;

            dailyRow["총 검사 수"] = Convert.ToInt32(dailyRow["통과 수"]) + Convert.ToInt32(dailyRow["실패 수"]);
            double dailyPassRate = Convert.ToInt32(dailyRow["총 검사 수"]) > 0 ?
                (Convert.ToDouble(dailyRow["통과 수"]) / Convert.ToInt32(dailyRow["총 검사 수"])) * 100 : 0;
            dailyRow["통과율"] = Math.Round(dailyPassRate, 2);

            // 차트 업데이트
            UpdateCharts();
        }

        private void UpdateCharts()
        {
            // 차트 업데이트 로직 구현
            // (Windows Forms의 Chart 컨트롤을 사용하여 구현)
        }

        private void btnRunAutoTest_Click(object sender, EventArgs e)
        {
            if (!serialConnected)
            {
                MessageBox.Show("먼저 장치에 연결하세요.", "연결 필요", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            // 선택된 테스트 항목 확인
            List<string> selectedTests = new List<string>();
            foreach (object item in lstTests.CheckedItems)
            {
                selectedTests.Add(item.ToString());
            }

            if (selectedTests.Count == 0)
            {
                MessageBox.Show("실행할 테스트를 하나 이상 선택하세요.", "테스트 선택 필요", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            try
            {
                Cursor = Cursors.WaitCursor;
                
                // 결과를 저장할 딕셔너리
                Dictionary<string, object> results = new Dictionary<string, object>();
                Dictionary<string, object> summary = new Dictionary<string, object>();
                
                summary["총 검사 수"] = selectedTests.Count;
                summary["통과"] = 0;
                summary["실패"] = 0;
                summary["통과율"] = 0.0;
                summary["시작 시간"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                
                DateTime startTime = DateTime.Now;
                
                // 테스트 시퀀스 실행
                foreach (string test in selectedTests)
                {
                    string testName = $"{test} 검사";
                    progAutoTest.Value = (selectedTests.IndexOf(test) + 1) * 100 / selectedTests.Count;
                    lblTestStatus.Text = $"{testName} 실행 중...";
                    Application.DoEvents();
                    
                    // 테스트 실행
                    try
                    {
                        string result = TestFunctions.RunTest(test, serialHandler);
                        
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
                            
                        // 테스트 결과 테이블 및 통계 업데이트
                        UpdateTestStatistics(testName, result);
                        
                        // 제품 정보
                        Dictionary<byte, string> productTypes = new Dictionary<byte, string>
                        {
                            { 0x5B, "조명 스위치" },
                            { 0x5C, "콘센트 스위치" },
                            { 0x5D, "디밍 스위치" }
                        };
                        
                        byte prodType = Convert.ToByte(configData["product_type"]);
                        string currentProduct = productTypes.ContainsKey(prodType) ? productTypes[prodType] : "알 수 없음";
                        
                        // 테스트 결과 추가
                        DataRow row = testResults.NewRow();
                        row["테스트"] = testName;
                        row["결과"] = result;
                        row["시간"] = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                        row["제품 종류"] = currentProduct;
                        row["조명 회로"] = configData["light_circuits"];
                        row["콘센트 회로"] = configData["outlet_circuits"];
                        row["디밍 종류"] = configData["dimming_type"];
                        testResults.Rows.Add(row);
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
                DateTime endTime = DateTime.Now;
                summary["종료 시간"] = endTime.ToString("yyyy-MM-dd HH:mm:ss");
                TimeSpan duration = endTime - startTime;
                summary["소요 시간"] = $"{duration.TotalSeconds:F2}초";
                
                // 통과율 계산
                int totalTests = Convert.ToInt32(summary["총 검사 수"]);
                if (totalTests > 0)
                {
                    summary["통과율"] = (Convert.ToDouble(summary["통과"]) / totalTests) * 100;
                }
                
                // 테스트 결과 표시
                lblTestStatus.Text = "테스트 완료";
                progAutoTest.Value = 100;
                
                // 결과 메시지
                string resultMessage = $"테스트 완료\n" +
                                      $"총 검사 수: {summary["총 검사 수"]}\n" +
                                      $"통과: {summary["통과"]}\n" +
                                      $"실패: {summary["실패"]}\n" +
                                      $"통과율: {summary["통과율"]:F2}%\n" +
                                      $"소요 시간: {summary["소요 시간"]}";
                
                MessageBox.Show(resultMessage, "자동화 테스트 결과", MessageBoxButtons.OK, 
                    Convert.ToInt32(summary["실패"]) == 0 ? MessageBoxIcon.Information : MessageBoxIcon.Warning);
                
                // 데이터 그리드 업데이트
                dgvTestResults.DataSource = testResults;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"자동화 테스트 실행 중 오류 발생: {ex.Message}", "테스트 오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                Cursor = Cursors.Default;
            }
        }

        private void btnExportCSV_Click(object sender, EventArgs e)
        {
            if (testResults.Rows.Count == 0)
            {
                MessageBox.Show("내보낼 테스트 데이터가 없습니다.", "데이터 없음", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            SaveFileDialog saveDialog = new SaveFileDialog();
            saveDialog.Filter = "CSV 파일 (*.csv)|*.csv";
            saveDialog.Title = "테스트 결과 내보내기";
            saveDialog.FileName = $"test_results_{DateTime.Now:yyyyMMdd_HHmmss}.csv";

            if (saveDialog.ShowDialog() == DialogResult.OK)
            {
                try
                {
                    StringBuilder sb = new StringBuilder();

                    // 헤더 추가
                    string[] columnNames = testResults.Columns.Cast<DataColumn>().Select(column => column.ColumnName).ToArray();
                    sb.AppendLine(string.Join(",", columnNames));

                    // 데이터 추가
                    foreach (DataRow row in testResults.Rows)
                    {
                        string[] fields = row.ItemArray.Select(field => field.ToString()).ToArray();
                        sb.AppendLine(string.Join(",", fields));
                    }

                    File.WriteAllText(saveDialog.FileName, sb.ToString(), Encoding.UTF8);
                    MessageBox.Show("테스트 결과가 성공적으로 내보내졌습니다.", "내보내기 완료", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"파일 내보내기 중 오류 발생: {ex.Message}", "내보내기 오류", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void btnResetData_Click(object sender, EventArgs e)
        {
            DialogResult result = MessageBox.Show("정말로 모든 테스트 데이터를 초기화하시겠습니까?", "데이터 초기화 확인", 
                MessageBoxButtons.YesNo, MessageBoxIcon.Question);

            if (result == DialogResult.Yes)
            {
                // 모든 테스트 데이터 초기화
                testResults.Clear();
                dailyPassRate.Clear();
                testCountByType.Clear();

                // 데이터 그리드 및 차트 업데이트
                dgvTestResults.DataSource = testResults;
                UpdateCharts();

                MessageBox.Show("모든 테스트 데이터가 초기화되었습니다.", "초기화 완료", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        }

        // UI 컴포넌트 초기화 코드 (디자이너에서 생성)
        private void InitializeComponent()
        {
            // 여기에 UI 컴포넌트 초기화 코드가 들어갑니다.
            // Windows Forms 디자이너로 생성되는 부분입니다.
        }
    }
}