classdef TCPSendSocket < handle
   properties
      ip
      port
      socket
      message_format = 0;  % 1 = numpy array or dict of numpy arrays
                           % 2 = json message
   end
   methods
      function obj = TCPSendSocket(tcp_port, tcp_ip, message_format)
         if nargin == 3
            obj.ip = tcp_ip;
            obj.port = tcp_port;
            obj.socket = tcpip(tcp_ip, tcp_port, 'NetworkRole', 'server');
            obj.socket.ByteOrder = 'littleEndian';
            set(obj.socket, 'TransferDelay', 'off');
            obj.message_format = message_format;
         elseif nargin == 2
            obj.ip = tcp_ip;
            obj.port = tcp_port;
            obj.socket = tcpip(tcp_ip, tcp_port, 'NetworkRole', 'server');
            obj.socket.ByteOrder = 'littleEndian';
            set(obj.socket, 'TransferDelay', 'off');
            obj.message_format = 2;
         else
            error('Need to supply at least tcp_port, tcp_ip');
         end
      end
      
      function start(self)
         fopen(self.socket);
         fwrite(self.socket, self.message_format, 'int32');
      end
      
      function stop(self)
        fclose(self.socket);
      end
      
      function send_data(self, data)
         encoded = jsonencode(data);
         length = strlength(encoded);
         fwrite(self.socket, length, 'int32');
         fwrite(self.socket, encoded, 'char');
      end
   end
end