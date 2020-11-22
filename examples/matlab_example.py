from DataSocket import TCPSendSocket, JSON, TCPReceiveSocket
import time
import numpy as np
import threading
import sys

send_port = 4242
receive_port = 4343
ip = '0.0.0.0'


# define function to print the echo back from matlab
def print_data(data):
    print(data)


# create a send and receive socket
send_socket = TCPSendSocket(tcp_port=send_port, tcp_ip='', send_type=JSON)
rec_socket = TCPReceiveSocket(tcp_port=receive_port, handler_function=print_data, receive_as_raw=False)

# start the sockets
send_socket.start()
rec_socket.start()

stop_flag = threading.Event()


def send_sig():
    while not stop_flag.is_set():
        send_socket.send_data({'data': np.random.random((4, 4)).tolist()})
        time.sleep(0.5)


thread = threading.Thread(target=send_sig)
thread.start()

input('Press enter to shutdown.')
stop_flag.set()
thread.join()

# close the sockets
rec_socket.stop()
send_socket.stop()
sys.exit()
