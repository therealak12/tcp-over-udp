import enum

MSS = 400
DEFAULT_SS_THRESHOLD = 8
BUFF_SIZE = 1024
UDP_IP = 'localhost'
UDP_PORT = 8003
UDP_ADDRESS = (UDP_IP, UDP_PORT)
ALPHA = 0.125
BETA = 0.25


class ConnectionState(enum.Enum):
    CLOSED, LISTEN, SYN_RECEIVED, SYN_SENT, ESTABLISHED, FIN_RECEIVED, CLOSE_WAIT, LAST_ACK, FIN_WAIT_1, FIN_WAIT_2 = \
        range(1, 11)


class Packet:
    def __init__(self, source_address, dest_address, seq_num, ack_num, ACK, FIN, SYN, data, wnd_size=0):
        self.source_address = source_address
        self.dest_address = dest_address
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.ACK = ACK
        self.SYN = SYN
        self.FIN = FIN
        self.wnd_size = wnd_size
        self.data = data
        self.checksum = self.find_checksum()
        self.header_len = 40
        self.URG = 0
        self.PSH = 0
        self.RST = 0
        self.reserved_bits = 0
        self.urgent_pointer = 0

    def set_flags(self, SYN=0, ACK=0, FIN=0):
        self.SYN = SYN
        self.ACK = ACK
        self.FIN = FIN

    def find_checksum(self):
        ans = 0
        if hasattr(self, 'checksum'):
            return self.checksum
        return 10
