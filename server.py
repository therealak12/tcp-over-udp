import io
import pickle
import socket
import time
import random

from PIL import Image

from common import ConnectionState, BUFF_SIZE, UDP_ADDRESS, Packet


class Server:
    def __init__(self):
        self.STATE = ConnectionState.CLOSED
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.packet = Packet(0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.img_bytes = bytearray()
        self.client_address = None

    def listen(self):
        self.sock.bind(UDP_ADDRESS)
        self.STATE = ConnectionState.LISTEN

    def handshake(self):
        if self.STATE == ConnectionState.LISTEN:
            data, address = self.sock.recvfrom(BUFF_SIZE)
            packet = pickle.loads(data)
            if packet.SYN == 1:
                self.STATE = ConnectionState.SYN_RECEIVED
                self.packet.set_flags(ACK=1, SYN=1)
                self.sock.sendto(pickle.dumps(self.packet), address)
                self.handshake()
        elif self.STATE == ConnectionState.SYN_RECEIVED:
            data, address = self.sock.recvfrom(BUFF_SIZE)
            packet = pickle.loads(data)
            if packet.ACK == 1:
                self.STATE = ConnectionState.ESTABLISHED
                print('Connection Established')

    def receive_image(self):
        packet, address = self.sock.recvfrom(BUFF_SIZE)
        self.client_address = address
        packet = pickle.loads(packet)
        buffer = {}
        last_saved = -1
        while packet.FIN != 1:
            fail = random.randint(-10, 10)
            if fail < 0:
                self.sock.recvfrom(BUFF_SIZE)
            if packet.find_checksum() == packet.checksum:
                if last_saved + 1 == packet.seq_num:
                    self.img_bytes += packet.data
                    last_saved += 1
                    while str(last_saved) in buffer:
                        self.img_bytes += buffer[str(last_saved)]
                        last_saved += 1
                else:
                    buffer[str(packet.seq_num)] = packet.data
                print('Server is sending ACK for: ', packet.seq_num)
                self.packet.set_flags(ACK=1)
                self.packet.ack_num = packet.seq_num
                self.sock.sendto(pickle.dumps(self.packet), address)
            packet, address = self.sock.recvfrom(BUFF_SIZE)
            packet = pickle.loads(packet)
        while str(last_saved + 1) in buffer:
            self.img_bytes += buffer[str(last_saved + 1)]
            last_saved += 1

    def save_image(self):
        image = Image.open(io.BytesIO(self.img_bytes))
        image.save('rcvd_image.jpg')

    def terminate(self):
        self.packet.set_flags(ACK=1)
        self.sock.sendto(pickle.dumps(self.packet), self.client_address)
        time.sleep(0.0001)
        self.packet.set_flags(FIN=1)
        self.sock.sendto(pickle.dumps(self.packet), self.client_address)
        print('Connection terminated.')


server = Server()
server.listen()
server.handshake()
server.receive_image()
server.save_image()
server.terminate()
