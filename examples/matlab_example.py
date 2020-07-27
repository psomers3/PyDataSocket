from DataSocket import TCPSendSocket, JSON, TCPReceiveSocket
import time
import numpy as np


send_port = 4242
receive_port = 4343
ip = '0.0.0.0'


# define function to print the echo back from matlab
def print_data(data):
    print(data)


# create a send and receive socket
send_socket = TCPSendSocket(tcp_port=send_port, tcp_ip=ip, send_type=JSON)
rec_socket = TCPReceiveSocket(tcp_port=receive_port, handler_function=print_data)

# start the sockets
send_socket.start()
rec_socket.start()

# wait 5 seconds to give time to start the matlab script
time.sleep(5)

for i in range(10):
    # send a random 4x4 numpy array to matlab
    send_socket.send_data(np.random.random((4, 4)))
    time.sleep(0.5)

# close the sockets
rec_socket.stop()
send_socket.stop()
exit()
