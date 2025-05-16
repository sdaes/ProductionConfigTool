import datetime

def get_current_datetime_bytes():
    """
    Get current date and time formatted according to the protocol
    
    Returns:
        list: 4 bytes representing year (offset from 2020), month, day, hour, minute
    """
    now = datetime.datetime.now()
    year_offset = now.year - 2020
    
    # Format: 
    # byte 0: bits[0~3]: month, bits[4~7]: year offset from 2020
    # byte 1: day
    # byte 2: hour
    # byte 3: minute
    
    byte0 = ((year_offset & 0x0F) << 4) | (now.month & 0x0F)
    byte1 = now.day & 0xFF
    byte2 = now.hour & 0xFF
    byte3 = now.minute & 0xFF
    
    return [byte0, byte1, byte2, byte3]

def extract_datetime_from_bytes(byte_array, start_index=29):
    """
    Extract date and time from byte array
    
    Args:
        byte_array (bytes): Byte array containing date and time
        start_index (int): Starting index of date/time bytes
        
    Returns:
        datetime: Extracted datetime object
    """
    year_month = byte_array[start_index]
    day = byte_array[start_index + 1]
    hour = byte_array[start_index + 2]
    minute = byte_array[start_index + 3]
    
    year = 2020 + ((year_month >> 4) & 0x0F)
    month = year_month & 0x0F
    
    return datetime.datetime(year, month, day, hour, minute)

def calculate_checksum_xor(data):
    """
    Calculate XOR checksum of data
    
    Args:
        data (bytes): Data to calculate checksum for
        
    Returns:
        int: XOR checksum
    """
    result = 0
    for byte in data:
        result ^= byte
    return result

def calculate_checksum_add(data):
    """
    Calculate ADD checksum of data (sum of all bytes, keep only lower byte)
    
    Args:
        data (bytes): Data to calculate checksum for
        
    Returns:
        int: ADD checksum (lower byte only)
    """
    result = sum(data) & 0xFF
    return result

def validate_hex_string(hex_str):
    """
    Validate if string is a valid hex string
    
    Args:
        hex_str (str): String to validate
        
    Returns:
        bool: True if valid hex string, False otherwise
    """
    if not hex_str:
        return False
    
    try:
        int(hex_str, 16)
        return True
    except ValueError:
        return False
