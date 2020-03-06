from threading import Event, Thread
import select
from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY, SOL_SOCKET, SO_REUSEADDR, SO_REUSEPORT
import time
from io import BytesIO
import numpy as np
import os
import struct


class NumpySocket(object):
    def __init__(self, tcp_port, tcp_ip=''):
        self.data_to_send = b'0'
        self.port = tcp_port
        self.ip = tcp_ip
        self.new_value_available = Event()
        self.thread = Thread(target=self.run)
        self.stop_thread = Event()
        self.connected = False
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind((tcp_ip, tcp_port))
        self.socket_accept_thread = Thread(target=self._socket_accept)
        self.connection = None

    def _socket_accept(self):
        self.connection, client_address = self.socket.accept()

    def run(self):
        while True:
            while not self.connected:
                if self.stop_thread.is_set():
                    break
                self.socket = socket(AF_INET, SOCK_STREAM)
                self.socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
                self.socket.bind((self.ip, self.port))
                self.socket.setblocking(0)
                print('listening on port ', self.port)
                self.socket.listen(1)
                while not self.connected:
                    if self.stop_thread.is_set():
                        return
                    try:
                        self.connection, client_address = self.socket.accept()
                    except:
                        continue
                    self.connected = True

            while not self.new_value_available.is_set():
                time.sleep(0.0001)
            if self.stop_thread.is_set():
                return
            self.send_data()
            self.new_value_available.clear()

    def send_data(self):
        data_as_numpy = np.asarray(self.data_to_send)
        # print(np.max(data_as_numpy))
        f = BytesIO()
        np.savez_compressed(f, data=data_as_numpy)

        # determine file size in bytes
        f.seek(0, os.SEEK_END)
        size = f.tell()
        try:
            self.connection.send(struct.pack('I', size))
            f.seek(0)
            self.connection.sendall(f.read())  # Send data
        except Exception as e:
            print(e)
            self.socket.close()
            self.connected = False

    def shutdown(self):
        self.stop_thread.set()
        try:  # in case the thread wasn't started
            self.thread.join()
            self.socket.close()
        except:
            pass
