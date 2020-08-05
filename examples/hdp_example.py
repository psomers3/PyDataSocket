from DataSocket import TCPSendSocket, TCPReceiveSocket, HDF
import time
from threading import Thread


number_of_messages = 5  # number of sample messages to send
port = 4001  # TCP port to use


# define a function to send data across a TCP socket
def sending_function():
    send_socket = TCPSendSocket(tcp_port=port, send_type=HDF, verbose=True)
    send_socket.start(blocking=True)

    for i in range(number_of_messages):
        send_socket.send_data({'data': "The value of i is now " + str(i)})
        time.sleep(0.5)

    print("closing send socket.")
    send_socket.stop()


# define a function to receive and print data from a TCP socket
def receiving_function():
    num_messages_received = [0]

    # function to run when a new piece of data is received
    def print_value(data):
        print("value recieved: ", data)
        num_messages_received[0] = 1 + num_messages_received[0]

    rec_socket = TCPReceiveSocket(tcp_port=port, handler_function=print_value)
    rec_socket.start(blocking=True)

    while num_messages_received[0] < number_of_messages:
        # add delay so this loop does not unnecessarily tax the CPU
        time.sleep(0.25)

    print("closing receive socket.")
    rec_socket.stop()


if __name__ == '__main__':
    # define separate threads to run the sockets simultaneously
    send_thread = Thread(target=sending_function)
    rec_thread = Thread(target=receiving_function)

    rec_thread.start()
    send_thread.start()

    send_thread.join()
    rec_thread.join()
