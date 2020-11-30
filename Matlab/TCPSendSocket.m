classdef TCPSendSocket < handle
   properties
      ip
      port
      socket
      message_format = 0;  % 1 = numpy array or dict of numpy arrays
                           % 2 = json message
                           % 3 = HDF message
                           % 4 = raw data
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
         obj.socket.OutputBufferSize = 131072;
      end

      function start(self)
         is_started = false;
          while ~is_started
              try
                  fopen(self.socket);
              catch
                  continue
              end
              is_started = true;
          end
          if ~(self.message_format == 4)
            fwrite(self.socket, self.message_format, 'int32');
          end
      end

      function stop(self)
        fclose(self.socket);
      end

      function send_data(self, data)
         if ~(self.message_format == 4)
             encoded = jsonencode(data);
             length = strlength(encoded);
             fwrite(self.socket, length, 'int32');
             fwrite(self.socket, encoded, 'char');
         else
             fwrite(self.socket, data)
         end

      end
   end
end