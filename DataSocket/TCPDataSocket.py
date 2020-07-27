from threading import Event, Thread, Lock
from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY, SOL_SOCKET, SO_REUSEADDR
import time
from io import BytesIO
import numpy as np
import os
import struct
import json


NUMPY = 1
JSON = 2


def _get_socket():
    new_socket = socket(AF_INET, SOCK_STREAM)
    new_socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
    new_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    return new_socket


class TCPSendSocket(object):
    def __init__(self, tcp_port, tcp_ip='localhost', send_type=NUMPY, verbose=True):
        self.send_type = send_type
        self.data_to_send = b'0'
        self.port = int(tcp_port)
        self.ip = tcp_ip
        self.new_value_available = Event()
        self.thread = Thread(target=self.run)
        self.stop_thread = Event()
        self.connected = False
        self.socket = _get_socket()
        self.socket.bind((self.ip, self.port))
        self.connection = None
        self.verbose = verbose

    def _socket_accept(self):
        self.connection, client_address = self.socket.accept()

    def run(self):
        while True:
            while not self.connected:
                if self.stop_thread.is_set():
                    break
                self.socket = _get_socket()
                self.socket.bind((self.ip, self.port))
                self.socket.setblocking(0)
                if self.verbose:
                    print('listening on port ', self.port)
                self.socket.listen(1)
                while not self.connected:
                    if self.stop_thread.is_set():
                        return
                    try:
                        self.connection, client_address = self.socket.accept()
                    except BlockingIOError:
                        continue
                    self.connected = True
                    type_msg = struct.pack('I', self.send_type)
                    self.connection.sendall(type_msg)

            while not self.new_value_available.is_set():
                time.sleep(0.0001)
                if self.stop_thread.is_set():
                    return
            if self.stop_thread.is_set():
                return
            self._send_data()
            self.new_value_available.clear()

    def send_data(self, data):
        self.data_to_send = data
        self.new_value_available.set()

    def _send_data(self):
        if self.send_type == NUMPY:
            if isinstance(self.data_to_send, dict):
                for key in self.data_to_send.keys():
                    self.data_to_send[key] = np.asarray(self.data_to_send[key])
                f = BytesIO()
                np.savez_compressed(f, **self.data_to_send)
            else:
                data_as_numpy = np.asarray(self.data_to_send)
                # print(np.max(data_as_numpy))
                f = BytesIO()
                np.savez_compressed(f, data=data_as_numpy)

            # determine file size in bytes
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(0)
            f = f.read()

        elif self.send_type == JSON:
            try:
                f = json.dumps(self.data_to_send).encode()
            except TypeError:
                try:
                    f = json.dumps(self.data_to_send.tolist()).encode()
                except TypeError as e:
                    print(e)

            size = len(f)

        try:
            self.connection.send(struct.pack('I', size))
            self.connection.sendall(f)  # Send data
        except ConnectionError as e:
            if self.verbose:
                print(e)
            self.socket.close()
            self.connected = False

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_thread.set()
        if self.thread.is_alive():
            self.thread.join()
        self.socket.close()


# a client socket
class TCPReceiveSocket(object):
    def __init__(self, tcp_port, handler_function=None, tcp_ip='localhost', verbose=True):
        if handler_function is None:
            def pass_func(data):
                pass
            handler_function = pass_func

        if not callable(handler_function):
            raise ValueError("Handler function must be a callable function taking one input.")

        self.verbose = verbose
        self.handler_function = handler_function
        self._new_data = None
        self._new_data_lock = Lock()
        self.new_data_flag = Event()
        self.handler_thread = Thread(target=self._handler)
        self.socket = _get_socket()
        self.thread = Thread(target=self.recieve_data)
        self.port = int(tcp_port)
        self.ip = tcp_ip
        self.block_size = 0
        self.is_connected = False
        self.shut_down_flag = Event()
        self.data_mode = None

    @property
    def new_data(self):
        with self._new_data_lock:
            return self._new_data

    @new_data.setter
    def new_data(self, data):
        with self._new_data_lock:
            self._new_data = data

    def start(self):
        self.thread.start()

    def stop(self):
        self.shut_down_flag.set()
        if self.thread.is_alive():
            self.thread.join()
        if self.handler_thread.is_alive():
            self.handler_thread.join()
        self.shut_down_flag.clear()
        self.socket.close()
        self.socket = _get_socket()

    def initialize(self):
        while not self.is_connected and not self.shut_down_flag.is_set():
            try:
                self.socket.connect((self.ip, self.port))
            except (ConnectionError, OSError) as e:
                # print(e)
                self.socket = _get_socket()
                time.sleep(0.001)
                continue
            if self.verbose:
                print("connected on port ", self.port)
            self.is_connected = True

            bytes = self.socket.recv(4)
            data_type = struct.unpack('I', bytes)[0]

            if data_type == NUMPY:
                self.data_mode = NUMPY
                if self.verbose:
                    print('Expecting numpy files on receive.')
            elif data_type == JSON:
                self.data_mode = JSON
                if self.verbose:
                    print('Expecting json message on receive.')

            self.new_data_flag.clear()
            self.handler_thread.start()

    def recieve_data(self):
        self.initialize()
        while self.is_connected and not self.shut_down_flag.is_set():
            toread = 4
            buf = bytearray(toread)
            view = memoryview(buf)
            while toread:
                if self.shut_down_flag.is_set():
                    return
                try:
                    nbytes = self.socket.recv_into(view, toread)
                except OSError:
                    continue
                view = view[nbytes:]  # slicing views is cheap
                toread -= nbytes

            toread = int.from_bytes(buf, "little")
            buf = bytearray(toread)
            view = memoryview(buf)
            while toread:
                if self.shut_down_flag.is_set():
                    return
                try:
                    nbytes = self.socket.recv_into(view, toread)
                except OSError:
                    continue
                view = view[nbytes:]  # slicing views is cheap
                toread -= nbytes

            if self.data_mode == NUMPY:
                as_file = BytesIO(buf)
                as_file.seek(0)
                try:
                    self.new_data = np.load(as_file)
                except OSError as e:
                    if self.verbose:
                        print(e)
                    continue
            elif self.data_mode == JSON:
                self.new_data = json.loads(buf.decode())

            self.new_data_flag.set()

    def _handler(self):
        while True:
            while not self.new_data_flag.is_set():
                if self.shut_down_flag.is_set():
                    return
                time.sleep(0.001)
            self.new_data_flag.clear()
            self.handler_function(self.new_data)
