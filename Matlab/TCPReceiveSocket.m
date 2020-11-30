classdef TCPReceiveSocket < handle
   properties
      callback
      ip
      port
      socket
      message_format = 0;  % 1 = numpy array or dict of numpy arrays
                           % 2 = json message
                           % 3 = HDF message
                           % 4 = Raw bytes
   end
   methods
      function obj = TCPReceiveSocket(tcp_port, tcp_ip, callback_function, receive_raw_data)
         if nargin >= 3
            obj.ip = tcp_ip;
            obj.port = tcp_port;
            obj.callback = callback_function;
            obj.socket = tcpip(tcp_ip, tcp_port, 'NetworkRole', 'client');
            obj.socket.ByteOrder = 'littleEndian';
            set(obj.socket,'BytesAvailableFcn', @obj.callback_wrapper);
            set(obj.socket,'ReadAsyncMode', 'continuous');
            set(obj.socket, 'TransferDelay', 'off');
            obj.socket.BytesAvailableFcnMode = 'byte';
            obj.socket.BytesAvailableFcnCount = 4;
            if nargin == 4
                if receive_raw_data
                    obj.message_format = 4;
                end
            end
         else
            error('Need to supply tcp_port, tcp_ip, and a callback_function')
         end
         obj.socket.InputBufferSize = 131072;
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
      end
      
      function stop(self)
        fclose(self.socket);
      end
      
      function callback_wrapper(self, socket, ~)
          if ~(self.message_format == 4)
              % return if for some reason this function got called and there
              % isn't enough data.
              if socket.BytesAvailable < 4
                return
              end
              % read in the length of the message
              length = fread(socket, 1, 'int32');

              if self.message_format == 0  % if this is the first message
                  self.message_format = length;

              elseif self.message_format == 1 % numpy format
                  error('numpy format not yet supported')
              
              elseif self.message_format == 2 % json format
                while socket.BytesAvailable < length
                    % wait till the entire message is there. Should possibly
                    % add a wait here to not tax the CPU, but realistically,
                    % the data is likely already there.
                end
                % Read in the message and decode from json
                data = jsondecode(fscanf(socket, '%c', double(length)));
                % Appy callback funtion supplied by user
                self.callback(data)
              end
          else % raw bytes
            if socket.BytesAvailable < 1
               return 
            end
            data = fread(socket, socket.BytesAvailable);
            self.callback(data);
          end
      end
   end
end