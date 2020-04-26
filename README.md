# PyDataSocket
This module provides an extremely easy to use python implementation of TCP Sockets for sending data. The supported data formats are anything that is json-serializable when using the ```DataSocket.JSON``` mode or anything that can be converted to a numpy array when using the ```DataSocket.NUMPY``` mode. This implementation utilizes threading so they are non-blocking. See the [examples](https://github.com/psomers3/PyDataSocket/tree/master/examples) for how to use.

## SendSocket()
The send socket is where the data form to use (JSON or NUMPY) is set and then informs the connecting RecieveSocket upon a successful connection. Data can be sent using ```SendSocket.send_data()```.

## ReceiveSocket()
The data recieved by the receive socket is accessed by assigning a function to ```handler_function``` upon creation that will be called everytime a new chunk of data is recieved. This is run on a separate thread, so it will not block more incoming data, but it is recommended to keep the assigned function as short as possible.
