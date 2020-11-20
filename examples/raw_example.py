from DataSocket import TCPSendSocket, JSON, TCPReceiveSocket, RAW
import time
import numpy as np
import threading
import struct
import sys

send_port = 4242
rec_port = 4242
ip = '127.0.0.1'


# define function to print the echo back from matlab
def print_data(data):
    print(data, "unpacked:", struct.unpack('ff', data))


# create a send and receive socket
send_socket = TCPSendSocket(tcp_port=send_port, tcp_ip=ip, send_type=RAW)
receive_socket = TCPReceiveSocket(tcp_port=rec_port, tcp_ip=ip, receive_as_raw=True, handler_function=print_data)

# start the sockets
send_socket.start()
receive_socket.start()
stop_flag = threading.Event()


def send_sig():
    while not stop_flag.is_set():
        data = np.random.random((1, 2)).tolist()[0]
        data_as_bytes = struct.pack('ff', *data)
        send_socket.send_data(data_as_bytes)
        time.sleep(0.5)


thread = threading.Thread(target=send_sig)
thread.start()

input('Press enter to shutdown.')
stop_flag.set()
thread.join()

# close the sockets
send_socket.stop()
receive_socket.stop()
sys.exit(0)