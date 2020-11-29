from .TCPDataSocket import TCPSendSocket, TCPReceiveSocket, NUMPY, JSON, HDF, RAW
from .UDPDataSocket import UDPReceiveSocket, UDPSendSocket


def install_matlab_socket_files(destination):
    """
    Copy the matlab DataSockets to a file directory of your choice.
    :param destination: file directory (str)
    """

    from pkg_resources import resource_filename
    import os
    from shutil import copyfile

    if not os.path.isdir(destination):
        raise NotADirectoryError("destination must be a valid directory")

    copyfile(resource_filename('DataSocket', 'Matlab/TCPReceiveSocket.m'),
             os.path.join(destination, 'TCPReceiveSocket.m'))
    copyfile(resource_filename('DataSocket', 'Matlab/TCPSendSocket.m'),
             os.path.join(destination, 'TCPSendSocket.m'))
