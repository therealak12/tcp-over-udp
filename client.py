import pickle
import socket
import threading
import time

from common import Packet, ConnectionState, UDP_ADDRESS, BUFF_SIZE, MSS


class Client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.STATE = ConnectionState.CLOSED
        self.packet = Packet(0, 0, 0, 0, 0, 0, 0, '', 0)
        self.packets = []
        self.acked = []
        self.last_sent = -1
        self.lock = threading.Lock()
        self.timeout = 1
        self.cwnd = 4
        self.sstr = 8
        self.ack_count = []

    def handshake(self):
        if self.STATE == ConnectionState.CLOSED:
            self.packet.set_flags(SYN=1)
            self.sock.sendto(pickle.dumps(self.packet), UDP_ADDRESS)
            self.STATE = ConnectionState.SYN_SENT
            self.handshake()
        elif self.STATE == ConnectionState.SYN_SENT:
            data, address = self.sock.recvfrom(BUFF_SIZE)
            packet = pickle.loads(data)
            if packet.SYN == 1 and packet.ACK == 1:
                self.packet.set_flags(ACK=1)
                self.sock.sendto(pickle.dumps(self.packet), UDP_ADDRESS)
                self.STATE = ConnectionState.ESTABLISHED
                print('Connection Established')

    def set_packets(self):
        with open('snd_img.jpg', 'rb')as img_f:
            img_bytes = bytearray(img_f.read())
            index = 0
            while index + MSS < len(img_bytes):
                self.packets.append(img_bytes[index:index + MSS])
                index += MSS
            self.packets.append(img_bytes[index:])
            self.acked = [False] * len(self.packets)
            self.ack_count = [0] * len(self.packets)

    def send_image(self):
        for i in range(self.last_sent + 1, min(self.cwnd, len(self.packets))):
            self.send_packet(i)
            self.last_sent += 1
        while True:
            packet, address = self.sock.recvfrom(BUFF_SIZE)
            packet = pickle.loads(packet)
            if packet.ACK == 1:
                self.on_new_ack(packet)
            for i in range(len(self.packets)):
                if not self.acked[i]:
                    break
            else:
                self.terminate()
                break
            for i in range(self.last_sent + 1, min(self.cwnd, len(self.packets))):
                self.send_packet(i)
                self.last_sent += 1

    def on_new_ack(self, packet):
        print('Received ACK for: ', packet.ack_num)
        self.ack_count[packet.ack_num] += 1
        if self.ack_count[packet.ack_num] >= 3:
            self.sstr = self.cwnd / 2
            self.cwnd = 1
        if not self.acked[packet.ack_num]:
            self.acked[packet.ack_num] = True
            if self.cwnd <= self.sstr / 2:
                self.cwnd *= 2
            else:
                self.cwnd += 1
            if self.last_sent + 1 < len(self.packets):
                self.send_packet(self.last_sent + 1)
                self.last_sent += 1

    def send_packet(self, seq_num):
        self.packet.set_flags()
        self.packet.data = self.packets[seq_num]
        self.packet.seq_num = seq_num
        self.sock.sendto(pickle.dumps(self.packet), UDP_ADDRESS)
        threading.Thread(target=self.count_down_for, args=(seq_num,)).start()

    def count_down_for(self, packet_num):
        time.sleep(self.timeout)
        if not self.acked[packet_num]:
            self.send_packet(packet_num)

    def terminate(self):
        print('Terminating connection.')
        self.packet.set_flags(FIN=1)
        self.packet.data = ''
        self.sock.sendto(pickle.dumps(self.packet), UDP_ADDRESS)
        packet, address = self.sock.recvfrom(BUFF_SIZE)
        packet = pickle.loads(packet)
        if packet.ACK == 1:
            packet, address = self.sock.recvfrom(BUFF_SIZE)
            packet = pickle.loads(packet)
            if packet.FIN == 1:
                print('Connection terminated.')


client = Client()
client.handshake()
client.set_packets()
client.send_image()
