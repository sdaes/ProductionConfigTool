using System;
using System.IO.Ports;
using System.Threading;

namespace ProductionTesterApp
{
    public class SerialHandler
    {
        private SerialPort serialPort;
        private bool isConnected = false;

        /// <summary>
        /// 시리얼 연결 핸들러 초기화
        /// </summary>
        /// <param name="portName">COM 포트 이름 (예: "COM3")</param>
        /// <param name="baudRate">통신 속도 (기본값: 115200)</param>
        /// <param name="timeout">읽기 타임아웃 (초 단위)</param>
        public SerialHandler(string portName, int baudRate = 115200, int timeout = 1)
        {
            try
            {
                serialPort = new SerialPort
                {
                    PortName = portName,
                    BaudRate = baudRate,
                    DataBits = 8,
                    Parity = Parity.None,
                    StopBits = StopBits.One,
                    ReadTimeout = timeout * 1000,
                    WriteTimeout = timeout * 1000
                };

                serialPort.Open();
                isConnected = true;
            }
            catch (Exception ex)
            {
                throw new Exception($"시리얼 포트 연결 실패: {ex.Message}");
            }
        }

        /// <summary>
        /// 데이터 패킷을 시리얼 연결을 통해 전송
        /// </summary>
        /// <param name="data">전송할 데이터 패킷</param>
        /// <returns>성공 여부</returns>
        public bool SendPacket(byte[] data)
        {
            if (!isConnected || serialPort == null)
                return false;

            try
            {
                serialPort.Write(data, 0, data.Length);
                return true;
            }
            catch (Exception)
            {
                return false;
            }
        }

        /// <summary>
        /// 시리얼 연결에서 응답 읽기
        /// </summary>
        /// <param name="expectedBytes">예상되는 바이트 수</param>
        /// <param name="timeout">타임아웃 (초 단위)</param>
        /// <returns>수신된 데이터</returns>
        public byte[] ReadResponse(int expectedBytes = 40, int timeout = 5)
        {
            if (!isConnected || serialPort == null)
                return null;

            try
            {
                // 기존 타임아웃 설정 임시 저장
                int originalTimeout = serialPort.ReadTimeout;
                serialPort.ReadTimeout = timeout * 1000;

                byte[] buffer = new byte[expectedBytes];
                int bytesRead = 0;
                DateTime startTime = DateTime.Now;

                // 예상 바이트 수만큼 읽거나 타임아웃까지 대기
                while (bytesRead < expectedBytes)
                {
                    if ((DateTime.Now - startTime).TotalSeconds > timeout)
                        break;

                    if (serialPort.BytesToRead > 0)
                    {
                        int count = serialPort.Read(buffer, bytesRead, Math.Min(serialPort.BytesToRead, expectedBytes - bytesRead));
                        bytesRead += count;
                    }
                    else
                    {
                        Thread.Sleep(10);
                    }
                }

                // 타임아웃 설정 복원
                serialPort.ReadTimeout = originalTimeout;

                if (bytesRead == 0)
                    return null;

                // 실제로 읽은 바이트 수에 맞게 배열 크기 조정
                if (bytesRead != expectedBytes)
                {
                    byte[] result = new byte[bytesRead];
                    Array.Copy(buffer, result, bytesRead);
                    return result;
                }

                return buffer;
            }
            catch (Exception)
            {
                return null;
            }
        }

        /// <summary>
        /// 명령 전송 및 응답 대기
        /// </summary>
        /// <param name="commandCode">명령 코드</param>
        /// <param name="data">명령과 함께 전송할 데이터 (선택사항)</param>
        /// <param name="waitForResponse">응답 대기 여부</param>
        /// <returns>응답 데이터 (waitForResponse가 true인 경우), 그렇지 않은 경우 null</returns>
        public byte[] SendCommand(byte commandCode, byte[] data = null, bool waitForResponse = true)
        {
            if (!isConnected || serialPort == null)
                return null;

            try
            {
                // 명령 패킷 구성
                byte[] commandPacket;
                if (data != null && data.Length > 0)
                {
                    commandPacket = new byte[data.Length + 1];
                    commandPacket[0] = commandCode;
                    Array.Copy(data, 0, commandPacket, 1, data.Length);
                }
                else
                {
                    commandPacket = new byte[] { commandCode };
                }

                // 명령 전송
                serialPort.Write(commandPacket, 0, commandPacket.Length);

                // 응답 대기
                if (waitForResponse)
                {
                    return ReadResponse();
                }

                return null;
            }
            catch (Exception)
            {
                return null;
            }
        }

        /// <summary>
        /// 장치 응답성 확인
        /// </summary>
        /// <returns>장치가 응답하는 경우 true, 그렇지 않은 경우 false</returns>
        public bool CheckDeviceStatus()
        {
            if (!isConnected || serialPort == null)
                return false;

            try
            {
                // 상태 확인 명령 전송 (0x01)
                byte[] response = SendCommand(0x01);
                return response != null && response.Length > 0;
            }
            catch (Exception)
            {
                return false;
            }
        }

        /// <summary>
        /// 시리얼 연결 닫기
        /// </summary>
        public void Close()
        {
            if (serialPort != null && serialPort.IsOpen)
            {
                serialPort.Close();
                isConnected = false;
            }
        }
    }
}