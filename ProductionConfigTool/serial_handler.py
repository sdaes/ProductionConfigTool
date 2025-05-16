import serial
import time
import streamlit as st

class SerialHandler:
    """
    Handler for serial communication with production line devices
    """
    
    def __init__(self, port, baudrate=115200, timeout=1):
        """
        Initialize the serial connection
        
        Args:
            port (str): COM port to connect to
            baudrate (int): Baud rate (default 115200)
            timeout (int): Read timeout in seconds
        """
        try:
            self.serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )
            
            # Wait for connection to establish
            time.sleep(0.5)
            
        except Exception as e:
            raise Exception(f"Serial port connection failed: {str(e)}")
    
    def send_packet(self, data):
        """
        Send a data packet over the serial connection
        
        Args:
            data (bytes): Data packet to send
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.serial.is_open:
            raise Exception("Serial port is not open")
        
        try:
            bytes_written = self.serial.write(data)
            return bytes_written == len(data)
        except Exception as e:
            raise Exception(f"Failed to send data: {str(e)}")
    
    def read_response(self, expected_bytes=40, timeout=5):
        """
        Read a response from the serial connection
        
        Args:
            expected_bytes (int): Number of bytes to read
            timeout (int): Timeout in seconds
            
        Returns:
            bytes: Received data
        """
        if not self.serial.is_open:
            raise Exception("Serial port is not open")
        
        start_time = time.time()
        buffer = bytearray()
        
        # Wait until we receive the expected number of bytes or timeout
        while (len(buffer) < expected_bytes) and (time.time() - start_time < timeout):
            if self.serial.in_waiting > 0:
                buffer += self.serial.read(self.serial.in_waiting)
            time.sleep(0.01)
        
        if len(buffer) < expected_bytes:
            raise Exception(f"Timeout waiting for response. Received {len(buffer)}/{expected_bytes} bytes")
        
        return bytes(buffer)
    
    def send_command(self, command_code, data=None, wait_for_response=True):
        """
        Send a command and wait for response
        
        Args:
            command_code (int): Command code
            data (bytes): Optional data to send with command
            wait_for_response (bool): Whether to wait for a response
            
        Returns:
            bytes: Response data if wait_for_response is True, else None
        """
        # Create command packet
        packet = bytearray([0xDA, command_code])  # STX and command code
        
        if data:
            packet.extend(data)
        
        # Add packet length
        data_length = len(packet) - 2  # Subtract STX and command code
        packet.insert(2, data_length)
        
        # Add ETX
        packet.append(0x25)
        
        # Send the packet
        self.send_packet(packet)
        
        # Wait for response if required
        if wait_for_response:
            return self.read_response()
        
        return None
    
    def check_device_status(self):
        """
        Check if the device is responsive
        
        Returns:
            bool: True if device is responsive, False otherwise
        """
        try:
            # Send a simple status check command
            response = self.send_command(0x01)  # Assuming 0x01 is status check command
            
            # Verify the response has correct format
            if response and len(response) >= 3:
                if response[0] == 0xDA and response[-1] == 0x25:
                    return True
            
            return False
        except Exception:
            return False
    
    def close(self):
        """Close the serial connection"""
        if hasattr(self, 'serial') and self.serial.is_open:
            self.serial.close()
