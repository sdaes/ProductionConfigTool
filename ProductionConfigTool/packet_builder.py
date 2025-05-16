import time
import datetime

class PacketBuilder:
    """
    Builds a 40-byte packet according to the protocol specification
    for sending configuration settings to production line devices
    """
    
    def __init__(self, config_data):
        """
        Initialize packet builder with configuration data
        
        Args:
            config_data (dict): Dictionary containing configuration parameters
        """
        self.config_data = config_data
    
    def build_packet(self):
        """
        Build the 40-byte packet according to the protocol specification
        
        Returns:
            bytes: 40-byte packet
        """
        # Initialize 40-byte array with zeros
        packet = bytearray(40)
        
        # Fill in packet data according to protocol
        
        # [0] STX
        packet[0] = 0xDA
        
        # [1] Product type
        packet[1] = self.config_data['product_type']
        
        # [2]~[3] ID (MAC address lower 2 bytes)
        mac_bytes = bytes.fromhex(self.config_data['mac_address'])
        packet[2] = mac_bytes[0] if len(mac_bytes) > 0 else 0
        packet[3] = mac_bytes[1] if len(mac_bytes) > 1 else 0
        
        # [4] Data length is bytes [5]~[36] (32 bytes)
        packet[4] = 32
        
        # [5] Circuit configuration
        packet[5] = (
            (self.config_data['light_circuits'] & 0x0F) |        # bits 0-3: light circuits
            ((self.config_data['outlet_circuits'] & 0x03) << 4) | # bits 4-5: outlet circuits
            ((self.config_data['dimming_type'] & 0x03) << 6)      # bits 6-7: dimming type
        )
        
        # [6] Delay time
        packet[6] = self.config_data['delay_time'] & 0xFF
        
        # [7] SUB ID
        packet[7] = self.config_data['sub_id'] & 0xFF
        
        # [8] IR presence
        packet[8] = self.config_data['ir_present'] & 0x01
        
        # [9] Scenario
        packet[9] = self.config_data['scenario'] & 0x07
        
        # [10] Communication company
        packet[10] = self.config_data['comm_company'] & 0x07
        
        # [11] 3Way
        packet[11] = self.config_data['three_way'] & 0x01
        
        # [12] Overload protection and emergency call
        packet[12] = (
            (self.config_data['overload_protection'] & 0x0F) |   # bits 0-3: overload protection
            ((self.config_data['emergency_call'] & 0x0F) << 4)   # bits 4-7: emergency call
        )
        
        # [13]~[16] Outlet 1 values
        outlet1_learn = self.config_data['outlet1_learn_value']
        outlet1_current = self.config_data['outlet1_current_value']
        
        packet[13] = outlet1_learn & 0xFF         # Low byte
        packet[14] = (outlet1_learn >> 8) & 0xFF  # High byte
        packet[15] = outlet1_current & 0xFF       # Low byte
        packet[16] = (outlet1_current >> 8) & 0xFF # High byte
        
        # [17]~[20] Outlet 2 values
        outlet2_learn = self.config_data['outlet2_learn_value']
        outlet2_current = self.config_data['outlet2_current_value']
        
        packet[17] = outlet2_learn & 0xFF         # Low byte
        packet[18] = (outlet2_learn >> 8) & 0xFF  # High byte
        packet[19] = outlet2_current & 0xFF       # Low byte
        packet[20] = (outlet2_current >> 8) & 0xFF # High byte
        
        # [21] Relay ON/OFF status
        packet[21] = self.config_data['relay_status'] & 0xFF
        
        # [22] Outlet 1 mode
        packet[22] = self.config_data['outlet1_mode'] & 0x01
        
        # [23] Outlet 2 mode
        packet[23] = self.config_data['outlet2_mode'] & 0x01
        
        # [24] Reserved (set to 0)
        packet[24] = 0
        
        # [25] Sleep mode
        packet[25] = self.config_data['sleep_mode'] & 0x01
        
        # [26] Delay mode
        packet[26] = self.config_data['delay_mode'] & 0x01
        
        # [27] Dimming current value
        packet[27] = self.config_data['dimming_value'] & 0xFF
        
        # [28] Color temperature current value
        packet[28] = self.config_data['color_temp_value'] & 0xFF
        
        # [29]~[32] Current date/time from Windows
        now = datetime.datetime.now()
        year_offset = now.year - 2020
        
        packet[29] = ((year_offset & 0x0F) << 4) | (now.month & 0x0F)  # Year (offset from 2020) and month
        packet[30] = now.day & 0xFF    # Day
        packet[31] = now.hour & 0xFF   # Hour
        packet[32] = now.minute & 0xFF # Minute
        
        # [33]~[34] Reserved (set to 0)
        packet[33] = 0
        packet[34] = 0
        
        # [35]~[36] Version information
        packet[35] = 0x03  # Version high byte
        packet[36] = 0x13  # Version low byte
        
        # [37] XOR checksum of bytes [6]~[36]
        xor_checksum = 0
        for i in range(6, 37):
            xor_checksum ^= packet[i]
        packet[37] = xor_checksum
        
        # [38] ADD checksum of bytes [6]~[36]
        add_checksum = 0
        for i in range(6, 37):
            add_checksum += packet[i]
        packet[38] = add_checksum & 0xFF  # Take only lower byte
        
        # [39] ETX
        packet[39] = 0x25
        
        return bytes(packet)
    
    def validate_packet(self, packet):
        """
        Validate packet checksums and structure
        
        Args:
            packet (bytes): Packet to validate
            
        Returns:
            bool: True if valid, False if invalid
        """
        if len(packet) != 40:
            return False
            
        # Check STX and ETX
        if packet[0] != 0xDA or packet[39] != 0x25:
            return False
            
        # Calculate and verify XOR checksum
        xor_checksum = 0
        for i in range(6, 37):
            xor_checksum ^= packet[i]
            
        if xor_checksum != packet[37]:
            return False
            
        # Calculate and verify ADD checksum
        add_checksum = 0
        for i in range(6, 37):
            add_checksum += packet[i]
            
        if (add_checksum & 0xFF) != packet[38]:
            return False
            
        return True
