from threading import Event, Thread, Lock
from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY, SOL_SOCKET, SO_REUSEADDR, error
import time
from io import BytesIO
import numpy as np
import os
import struct
import json
import h5py

NUMPY = 1
JSON = 2
HDF = 3
RAW = 4


def _get_socket():
    new_socket = socket(AF_INET, SOCK_STREAM)
    new_socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
    new_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    return new_socket


class TCPSendSocket(object):
    def __init__(self,
                 tcp_port,
                 tcp_ip='localhost',
                 send_type=NUMPY,
                 verbose=True,
                 as_server=True,
                 include_time=False,
                 as_daemon=True):
        """
        A TCP socket class to send data to a specific port and address.
        :param tcp_port: TCP port to use.
        :param tcp_ip: ip address to connect to.
        :param send_type: This is the data type used to send the data. DataSocket.NUMPY uses a numpy file to store the
               data for sending. This is ideal for large arrays. DataSocket.JSON converts the data to a json formatted string.
               JSON is best for smaller messages. DataSocket.HDF uses the HDF5 file format and performance is probably
               comparable to NUMPY. DataSocket.RAW expects a bytes object and sends it directly with no processing. The
               receiving socket must be manually set to receive raw data.
        :param verbose: Whether or not to print errors and status messages.
        :param as_server: Whether to run this socket as a server (default: True) or client. When run as a server, the
               socket supports multiple clients and sends each message to every connected client.
        :param include_time: Appends time.time() value when sending the data message.
        :param as_daemon: runs the underlying threads as daemon.
        """
        self.send_type = send_type
        self.data_to_send = b'0'
        self.port = int(tcp_port)
        self.ip = tcp_ip
        self.new_value_available = Event()
        self.stop_thread = Event()
        self.socket = _get_socket()
        self.verbose = verbose
        self.as_server = as_server
        self.include_time = include_time
        self.connected_clients = []
        self._gather_connections_thread = Thread(target=self._gather_connections, daemon=as_daemon)
        self.sending_thread = Thread(target=self._run, daemon=as_daemon)

    def send_data(self, data):
        """
        Send the data to the socket. Use an appropriate send_type for the data that will be sent (i.e. don't use JSON
        for a 500x500 numpy array).
        :param data: the format of data is very flexible. Supported formats include:
                     a single numerical value
                     a string
                     a list of json serializable values (when using JSON format)
                     a numpy array (best with the NUMPY send format)
                     a dict of values or numpy arrays
                        i.e.   data = {'data1': numpy_array1,
                                       'data2': numpy_array2}
        :return: Nothing
        """
        self.data_to_send = data
        self.new_value_available.set()

    def start(self, blocking=False):
        """
        Start the socket service.
        :param blocking: Will block the calling thread until a connection is established to at least one receiver.
        :return: Nothing
        """
        self._establish_connection()
        self.sending_thread.start()
        if blocking:
            while not len(self.connected_clients) > 0:
                time.sleep(0.05)

    def stop(self):
        """
        Stop the socket and it's associated threads.
        """
        self.stop_thread.set()
        if self._gather_connections_thread.is_alive():
            self._gather_connections_thread.join(timeout=2)
        if self.sending_thread.is_alive():
            self.sending_thread.join(timeout=2)
        self.socket.close()

    def _gather_connections(self):
        self.socket.bind((self.ip, self.port))
        self.socket.setblocking(0)
        if self.verbose:
            print('listening on port ', self.port)
        self.socket.listen(1)

        while not self.stop_thread.is_set():
            clients_to_remove = []
            for client in self.connected_clients:
                if not client[2]:
                    clients_to_remove.append(client)
            for client in clients_to_remove:
                self.connected_clients.remove(client)

            if self.stop_thread.is_set():
                return
            try:
                connection, client_address = self.socket.accept()
            except BlockingIOError:
                continue
            new_connection = [connection, client_address, True]
            self.connected_clients.append(new_connection)  # boolean is for connected
            if not self.send_type == RAW:
                type_msg = struct.pack('I', self.send_type)
                new_connection[0].sendall(type_msg)

    def _establish_connection(self):
        while not len(self.connected_clients) > 0:
            if self.stop_thread.is_set():
                break
            if self.as_server and not self._gather_connections_thread.is_alive():
                self._gather_connections_thread.start()
                break
            else:
                while not len(self.connected_clients) > 0:
                    try:
                        self.socket.connect((self.ip, self.port))
                    except (ConnectionError, OSError) as e:
                        self.socket = _get_socket()
                        time.sleep(0.001)
                        continue
                    self.connected_clients.append([self.socket, 0, True])
                    if not self.send_type == RAW:
                        type_msg = struct.pack('I', self.send_type)
                        self.socket.sendall(type_msg)

    def _run(self):
        while not self.stop_thread.is_set():
            while not self.new_value_available.is_set():
                time.sleep(0.0001)
                if self.stop_thread.is_set():
                    return
            if self.stop_thread.is_set():
                return
            self._send_data()
            self.new_value_available.clear()

    def _send_data(self):
        if len(self.connected_clients) < 1:
            return
        now = time.time()
        if self.send_type == NUMPY:
            if isinstance(self.data_to_send, dict):
                if self.include_time:
                    self.data_to_send['_time'] = now
                for key in self.data_to_send.keys():
                    self.data_to_send[key] = np.asarray(self.data_to_send[key])
                f = BytesIO()
                np.savez_compressed(f, **self.data_to_send)
            else:
                data_as_numpy = np.asarray(self.data_to_send)
                f = BytesIO()
                if self.include_time:
                    np.savez_compressed(f, data=data_as_numpy, _time=np.asarray(now))
                else:
                    np.savez_compressed(f, data=data_as_numpy)

            # determine file size in bytes
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(0)
            f = f.read()

        elif self.send_type == JSON:
            if self.include_time:
                data_as_dict = {'data': self.data_to_send, '_time': now}
                try:
                    f = json.dumps(data_as_dict).encode()
                except TypeError:
                    try:
                        data_as_dict['data'] = data_as_dict['data'].tolist()
                        f = json.dumps(data_as_dict).encode()
                    except TypeError as e:
                        print(e)
            else:
                try:
                    f = json.dumps(self.data_to_send).encode()
                except TypeError as e1:
                    try:
                        f = json.dumps(self.data_to_send.tolist()).encode()
                    except TypeError as e:
                        print(e1, e)

            size = len(f)
        elif self.send_type == HDF:
            f = BytesIO()
            h5f = h5py.File(f, 'w')
            if isinstance(self.data_to_send, dict):
                if self.include_time:
                    self.data_to_send['_time'] = now
                for key in self.data_to_send.keys():
                    h5f.create_dataset(key, data=self.data_to_send[key])
            else:
                if self.include_time:
                    h5f.create_dataset('data', data=self.data_to_send, _time=now)
                else:
                    h5f.create_dataset('data', data=self.data_to_send)

            h5f.close()
            # determine file size in bytes
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(0)
            f = f.read()

        elif self.send_type == RAW:
            size = None
            f = self.data_to_send
        [self._send_f(connection, size, f) for connection in self.connected_clients]

    def _send_f(self, connection, size, file):
        try:
            if not self.send_type == RAW:
                connection[0].send(struct.pack('I', size))
            connection[0].sendall(file)  # Send data
        except ConnectionError as e:
            if self.verbose:
                print(e)
            connection[2] = False


# a client socket
class TCPReceiveSocket(object):
    def __init__(self,
                 tcp_port,
                 handler_function=None,
                 tcp_ip='localhost',
                 verbose=True,
                 as_server=False,
                 receive_as_raw=False,
                 receive_buffer_size=4095,
                 as_daemon=True):
        """
        Receiving TCP socket to be used with TCPSendSocket.
        :param tcp_port: TCP port to use.
        :param handler_function: The handle to a function that will be called everytime a message is received. Must take
               one parameter that is the message. The message is exactly what was sent from TCPSendSocket.
               example:
                        def my_handler(received_data):
                            print(received_data)
        :param tcp_ip: ip address to connect to.
        :param verbose: Whether or not to print errors and status messages.
        :param as_server: Whether to run this socket as a server (default: True) or client. This needs to be opposite
                          whatever the SendSocket is configured to be.
        :param receive_as_raw: Whether or not the incoming data is just raw bytes or is a predefined format (JSON, NUMPY, HDF)
        :param receive_buffer_size: available buffer size in bytes when receiving messages
        :param as_daemon: runs underlying threads as daemon.
        """
        self.receive_buffer_size = receive_buffer_size
        self.receive_as_raw = receive_as_raw
        self.max_tcp_packet_size = 1408
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
        self.handler_thread = Thread(target=self._handler, daemon=as_daemon)
        self.socket = _get_socket()
        self.thread = Thread(target=self._run, daemon=as_daemon)
        self.port = int(tcp_port)
        self.ip = tcp_ip
        self.block_size = 0
        self.is_connected = False
        self.shut_down_flag = Event()
        self.data_mode = None
        self.as_server = as_server
        self.connection = None

    def start(self, blocking=False):
        """
        Start the socket service.
        :param blocking: Will block the calling thread until a connection is established.
        """
        self.thread.start()
        if blocking:
            while not self.is_connected:
                time.sleep(0.05)

    def stop(self):
        """
        Stop the socket and it's associated threads.
        """
        self.shut_down_flag.set()
        if self.thread.is_alive():
            self.thread.join(timeout=2)

        if self.handler_thread.is_alive():
            self.handler_thread.join(timeout=2)
        self.shut_down_flag.clear()
        self.socket.close()
        self.socket = _get_socket()

    @property
    def new_data(self):
        with self._new_data_lock:
            return self._new_data

    @new_data.setter
    def new_data(self, data):
        with self._new_data_lock:
            self._new_data = data

    def _establish_connection(self):
        while not self.is_connected:
            if self.shut_down_flag.is_set():
                break
            self.socket = _get_socket()
            if self.as_server:
                self.socket.bind((self.ip, self.port))
                self.socket.setblocking(False)
                if self.verbose:
                    print('listening on port ', self.port)
                self.socket.listen(1)
                while not self.is_connected:
                    if self.shut_down_flag.is_set():
                        return
                    try:
                        self.connection, client_address = self.socket.accept()
                    except BlockingIOError as e:
                        continue
                    self.is_connected = True
            else:

                while not self.is_connected:
                    try:
                        self.socket.connect((self.ip, self.port))
                    except (ConnectionError, OSError) as e:
                        # print(e)
                        self.socket = _get_socket()
                        time.sleep(0.001)
                        continue
                    self.connection = self.socket
                    self.is_connected = True

    def _initialize(self):
        while not self.is_connected and not self.shut_down_flag.is_set():
            self._establish_connection()
            if not self.receive_as_raw:
                try:
                    bytes_received = self.connection.recv(4)
                except BlockingIOError as e:
                    print(e)
                    time.sleep(0.25)
                    bytes_received = self.connection.recv(4)

                data_type = struct.unpack('I', bytes_received)[0]
            else:
                data_type = RAW

            if data_type == NUMPY:
                self.data_mode = NUMPY
                if self.verbose:
                    print('Expecting numpy files on receive.')
            elif data_type == JSON:
                self.data_mode = JSON
                if self.verbose:
                    print('Expecting json message on receive.')
            elif data_type == HDF:
                self.data_mode = HDF
                if self.verbose:
                    print('Expecting HDF5 files on receive.')
            elif data_type == RAW:
                self.data_mode = RAW
                if self.verbose:
                    print('Expecting raw data on receive.')

            self.new_data_flag.clear()
            if not self.handler_thread.is_alive():
                try:
                    self.handler_thread.start()
                except RuntimeError:
                    pass

    def _run(self):
        while not self.shut_down_flag.is_set():
            try:
                if self.receive_as_raw:
                    self._receive_data_raw()
                else:
                    self._receive_data()
            except BlockingIOError as e:
                print(e)
                self.is_connected = False

    def _receive_data_raw(self):
        self._initialize()
        buf = bytearray(self.receive_buffer_size)
        view = memoryview(buf)
        total_received = 0
        nbytes = 0

        while self.is_connected and not self.shut_down_flag.is_set():
            try:
                while nbytes != -1:
                    try:
                        nbytes = self.connection.recv_into(view, self.receive_buffer_size - total_received - 1)
                    except BlockingIOError as e:
                        if nbytes > 0 and nbytes % self.max_tcp_packet_size != 0:
                            raise e
                        elif nbytes == 0:
                            continue
                        else:
                            continue
                    if nbytes == 0:
                        self.is_connected = False
                        break

                    total_received += nbytes
                    view = view[nbytes:]  # slicing views is cheap

            except BlockingIOError as e:
                if total_received > 0:
                    nbytes = -1
                    self.new_data = bytes(buf[:total_received])
                    view = memoryview(buf)
                continue

            if nbytes == 0:
                self.is_connected = False
                continue
            nbytes = 0
            total_received = 0
            self.new_data_flag.set()

    def _receive_data(self):
        self._initialize()
        while self.is_connected and not self.shut_down_flag.is_set():
            toread = 4
            buf = bytearray(toread)
            view = memoryview(buf)
            while toread and self.is_connected:
                if self.shut_down_flag.is_set():
                    return
                try:
                    nbytes = self.connection.recv_into(view, toread)
                except OSError as e:
                    print(e)
                    self.is_connected = False
                    return
                if nbytes == 0:
                    self.is_connected = False
                    return
                view = view[nbytes:]  # slicing views is cheap
                toread -= nbytes

            toread = int.from_bytes(buf, "little")
            buf = bytearray(toread)
            view = memoryview(buf)
            while toread and self.is_connected:
                if self.shut_down_flag.is_set():
                    return
                try:
                    nbytes = self.connection.recv_into(view, toread)
                except OSError as e:
                    print(e)
                    self.is_connected = False
                    return
                if nbytes == 0:
                    self.is_connected = False
                    return
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

            elif self.data_mode == HDF:
                as_file = BytesIO(buf)
                as_file.seek(0)
                try:
                    data = h5py.File(as_file, 'r')
                    if len(data.keys()) > 1:
                        new_data = {}
                        for key in data.keys():
                            new_data[key] = np.array(data.get(key))
                    else:
                        new_data = np.array(data.get(list(data.keys())[0]))
                    self.new_data = new_data
                except OSError as e:
                    if self.verbose:
                        print(e)
                    continue

            self.new_data_flag.set()

    def _handler(self):
        while True:
            while not self.new_data_flag.is_set():
                if self.shut_down_flag.is_set():
                    return
                time.sleep(0.001)
            self.new_data_flag.clear()
            self.handler_function(self.new_data)
