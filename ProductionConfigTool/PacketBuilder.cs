using System;
using System.Collections.Generic;
using System.Linq;

namespace ProductionTesterApp
{
    public class PacketBuilder
    {
        private Dictionary<string, object> configData;
        private const byte STX = 0x02;  // 시작 문자
        private const byte ETX = 0x03;  // 종료 문자

        /// <summary>
        /// 패킷 빌더 초기화
        /// </summary>
        /// <param name="configData">설정 데이터 딕셔너리</param>
        public PacketBuilder(Dictionary<string, object> configData)
        {
            this.configData = configData;
        }

        /// <summary>
        /// 프로토콜 사양에 따라 40바이트 패킷 구성
        /// </summary>
        /// <returns>40바이트 패킷</returns>
        public byte[] BuildPacket()
        {
            byte[] packet = new byte[40];  // 40바이트 패킷

            // 1. STX (시작 문자)
            packet[0] = STX;

            // 2. 제품 유형
            packet[1] = Convert.ToByte(configData["product_type"]);

            // 3. MAC 주소 (마지막 2바이트)
            string macStr = configData["mac_address"].ToString();
            if (macStr.Length == 4)
            {
                packet[2] = Convert.ToByte(macStr.Substring(0, 2), 16);
                packet[3] = Convert.ToByte(macStr.Substring(2, 2), 16);
            }
            else
            {
                packet[2] = 0x00;
                packet[3] = 0x00;
            }

            // 4. 데이터 길이
            packet[4] = 33;  // STX, 제품유형, MAC 주소 2바이트, 데이터 길이, XOR, ADD, ETX를 제외한 길이

            // 5. 조명 회로 설정
            packet[5] = Convert.ToByte(configData["light_circuits"]);

            // 6. 콘센트 회로 설정
            packet[6] = Convert.ToByte(configData["outlet_circuits"]);

            // 7. 디밍 유형 설정
            packet[7] = Convert.ToByte(configData["dimming_type"]);

            // 8. 기타 설정 필드 (기본값으로 채우기)
            for (int i = 8; i < 36; i++)
            {
                packet[i] = 0x00;
            }

            // 9. 현재 날짜 및 시간
            DateTime now = DateTime.Now;
            packet[29] = (byte)(now.Year - 2020);  // 2020년 기준 오프셋
            packet[30] = (byte)now.Month;
            packet[31] = (byte)now.Day;
            packet[32] = (byte)now.Hour;
            packet[33] = (byte)now.Minute;

            // 10. XOR 체크섬
            packet[36] = CalculateChecksumXOR(packet, 1, 36);

            // 11. ADD 체크섬
            packet[37] = CalculateChecksumADD(packet, 1, 36);

            // 12. ETX (종료 문자)
            packet[38] = ETX;

            // 13. 더미 바이트 (0x00)
            packet[39] = 0x00;

            return packet;
        }

        /// <summary>
        /// 패킷 체크섬 및 구조 유효성 검사
        /// </summary>
        /// <param name="packet">검사할 패킷</param>
        /// <returns>유효한 경우 true, 그렇지 않은 경우 false</returns>
        public bool ValidatePacket(byte[] packet)
        {
            if (packet == null || packet.Length != 40)
                return false;

            // STX 및 ETX 확인
            if (packet[0] != STX || packet[38] != ETX)
                return false;

            // 체크섬 확인
            byte xorChecksum = CalculateChecksumXOR(packet, 1, 36);
            byte addChecksum = CalculateChecksumADD(packet, 1, 36);

            return packet[36] == xorChecksum && packet[37] == addChecksum;
        }

        /// <summary>
        /// XOR 체크섬 계산
        /// </summary>
        /// <param name="data">체크섬을 계산할 데이터</param>
        /// <param name="start">시작 인덱스</param>
        /// <param name="end">종료 인덱스 (포함)</param>
        /// <returns>XOR 체크섬</returns>
        private byte CalculateChecksumXOR(byte[] data, int start, int end)
        {
            byte result = 0;
            for (int i = start; i <= end; i++)
            {
                result ^= data[i];
            }
            return result;
        }

        /// <summary>
        /// ADD 체크섬 계산 (모든 바이트의 합, 하위 바이트만 유지)
        /// </summary>
        /// <param name="data">체크섬을 계산할 데이터</param>
        /// <param name="start">시작 인덱스</param>
        /// <param name="end">종료 인덱스 (포함)</param>
        /// <returns>ADD 체크섬 (하위 바이트만)</returns>
        private byte CalculateChecksumADD(byte[] data, int start, int end)
        {
            int sum = 0;
            for (int i = start; i <= end; i++)
            {
                sum += data[i];
            }
            return (byte)(sum & 0xFF);  // 하위 바이트만 유지
        }
    }
}