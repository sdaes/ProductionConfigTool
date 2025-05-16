using System;
using System.Text.RegularExpressions;

namespace ProductionTesterApp
{
    public static class Utils
    {
        /// <summary>
        /// 현재 날짜 및 시간을 프로토콜에 맞게 바이트 배열로 변환
        /// </summary>
        /// <returns>연도(2020년 기준 오프셋), 월, 일, 시, 분을 나타내는 5개의 바이트</returns>
        public static byte[] GetCurrentDateTimeBytes()
        {
            DateTime now = DateTime.Now;
            byte[] result = new byte[5];
            
            result[0] = (byte)(now.Year - 2020);  // 2020년 기준 오프셋
            result[1] = (byte)now.Month;
            result[2] = (byte)now.Day;
            result[3] = (byte)now.Hour;
            result[4] = (byte)now.Minute;
            
            return result;
        }
        
        /// <summary>
        /// 바이트 배열에서 날짜 및 시간 추출
        /// </summary>
        /// <param name="byteArray">날짜 및 시간을 포함하는 바이트 배열</param>
        /// <param name="startIndex">날짜/시간 바이트의 시작 인덱스</param>
        /// <returns>추출된 DateTime 객체</returns>
        public static DateTime ExtractDateTimeFromBytes(byte[] byteArray, int startIndex = 29)
        {
            if (byteArray == null || byteArray.Length < startIndex + 5)
                throw new ArgumentException("바이트 배열이 날짜/시간 데이터를 포함하지 않습니다.");
            
            int year = 2020 + byteArray[startIndex];     // 2020년 기준 오프셋
            int month = byteArray[startIndex + 1];
            int day = byteArray[startIndex + 2];
            int hour = byteArray[startIndex + 3];
            int minute = byteArray[startIndex + 4];
            
            return new DateTime(year, month, day, hour, minute, 0);
        }
        
        /// <summary>
        /// 데이터의 XOR 체크섬 계산
        /// </summary>
        /// <param name="data">체크섬을 계산할 데이터</param>
        /// <returns>XOR 체크섬</returns>
        public static byte CalculateChecksumXOR(byte[] data)
        {
            if (data == null || data.Length == 0)
                throw new ArgumentException("체크섬을 계산할 데이터가 없습니다.");
            
            byte result = 0;
            
            foreach (byte b in data)
            {
                result ^= b;
            }
            
            return result;
        }
        
        /// <summary>
        /// 데이터의 ADD 체크섬 계산 (모든 바이트의 합, 하위 바이트만 유지)
        /// </summary>
        /// <param name="data">체크섬을 계산할 데이터</param>
        /// <returns>ADD 체크섬 (하위 바이트만)</returns>
        public static byte CalculateChecksumADD(byte[] data)
        {
            if (data == null || data.Length == 0)
                throw new ArgumentException("체크섬을 계산할 데이터가 없습니다.");
            
            int sum = 0;
            
            foreach (byte b in data)
            {
                sum += b;
            }
            
            return (byte)(sum & 0xFF);  // 하위 바이트만 유지
        }
        
        /// <summary>
        /// 문자열이 유효한 16진수 문자열인지 검증
        /// </summary>
        /// <param name="hexStr">검증할 16진수 문자열</param>
        /// <returns>유효한 16진수 문자열인 경우 true, 그렇지 않은 경우 false</returns>
        public static bool ValidateHexString(string hexStr)
        {
            if (string.IsNullOrEmpty(hexStr))
                return false;
            
            // 16진수 문자열 패턴: 0-9, A-F, a-f만 포함
            return Regex.IsMatch(hexStr, "^[0-9A-Fa-f]+$");
        }
    }
}