global send_socket
send_socket = TCPSendSocket(4343, '0.0.0.0');
rec_socket = TCPReceiveSocket(4242,'127.0.0.1',@echo_back);
% use '127.0.0.1' for windows and 'localhost' for unix systems

'start send'
send_socket.start()
'start receive'
rec_socket.start()

pause(5) % arbitrarily stay open for 10 seconds to receive the messages
          % from python

send_socket.stop();
rec_socket.stop();

function echo_back(data)
    global send_socket;
    data  % print data
    send_socket.send_data(data);
end