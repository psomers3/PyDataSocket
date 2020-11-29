# PyDataSocket
This module provides an easy to use python implementation of TCP Sockets for sending and receiving data. This module tries to reduce the effort for the user in determining how to package the data to send and dealing with the socket setting and full package length, ect. These sockets have a few different modes as outlined below:

 - RAW - This mode expects the data to be sent to already be a bytes object. This can be done using tools such as the struct module or numpy.tostring() for numpy data.
 - JSON - This mode will automatically try to jsonize anything that is given to send/receive. This works well for varying data types (dictionaries with strings and numbers). This mode will slow down quite a bit if large messages are passed (i.e. 100x100 list of numbers).
 - NUMPY - This mode expects anything that can be converted to a numpy array using np.asarray() or a dictionary of the same (i.e. `{'array1': np.array, 'array2': np.array}`). This mode is better to use for sending large arrays, but it is still a little slow because it creates and sends a full numpy file.
 - HDF - This operates similarly to the NUMPY mode, but uses the H5py package instead.

 See the [examples](https://github.com/psomers3/PyDataSocket/tree/master/examples) for how to use. Here you will also find matlab and simulink examples to pair with sending data between python and matlab/simulink. The matlab versions of the TCPReceive/TCPSend sockets must be copied and added to matlab yourself. These only support the RAW and JSON formats.


## Install
- ```pip install PyDataSocket```

The matlab files can be installed to a specific directory using the `install_matlab_socket_files(destination)` function, where `destination` is the directory to install the files to.

## Usage
```python
from DataSocket import TCPReceiveSocket, TCPSendSocket, RAW, JSON, HDF, NUMPY, install_matlab_socket_files
```
These sockets are meant to bind to a single network ip and port  (i.e. 1 SendSocket connects to 1 ReceiveSocket). The exception to this is that when the TCPSendSocket is configured as a server (default setting) multiple TCPReceiveSockets may connect and each will receive the data. The sockets must be started after creation using `start()` and this may be set to block the calling script until connection by passing `blocking=True` to the start function.

The send socket is very simple in that it will take care of everything when data is passed to the `send_data()` method. The receiving socket requires a handling function to be passed on construction to `handler_function`. This function will be called everytime data is received and should expect one input (the entire data message, already decoded if using a mode other than RAW).


### TCPSendSocket
```python
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
```

### TCPReceiveSocket
```python
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
```

