from DataSocket import TCPSendSocket, RAW, TCPReceiveSocket
import time
import numpy as np
import threading
import sys


send_port = 4242
receive_port = 4343
ip = '0.0.0.0'


# define function to print the echo back from matlab
def print_data(data):
    print('length of returned array:', np.frombuffer(data, dtype='float32').shape[0])


# create a send and receive socket
send_socket = TCPSendSocket(tcp_port=send_port, tcp_ip='', send_type=RAW)
rec_socket = TCPReceiveSocket(tcp_port=receive_port, handler_function=print_data, receive_as_raw=True, as_server=True, receive_buffer_size=65536)

# start the sockets
send_socket.start()
rec_socket.start()

stop_flag = threading.Event()


def send_sig():
    while not stop_flag.is_set():
        data = np.random.random((100, 100))  # create 100x100 array of random numbers
        data_as_bytes = data.astype('float32').flatten().tostring()  # flatten it before sending
        send_socket.send_data(data_as_bytes)
        time.sleep(1)


thread = threading.Thread(target=send_sig)
thread.start()

input('Press enter to shutdown.')
stop_flag.set()
thread.join()

# close the sockets
rec_socket.stop()
send_socket.stop()
sys.exit()
