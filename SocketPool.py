#!/usr/bin/python


import sys
import socket
import keyvalue_pb2

MAX_REQUEST_SIZE = 10000

class SocketPool:

    # sending protobuf messages to other server's and clients
    def send_message_Protobuf(self, ip, port_num, message):
        try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, int(port_num)))
                sock.sendall(message)
                server_response = sock.recv(MAX_REQUEST_SIZE)
                sock.close()
                if server_response == "" :
                        # ERROR ! Empty response from server, probably the server is dead
                        return None
                else:
                        # unpack message and return
                        incoming_message = keyvalue_pb2.KeyValueMessage()
                        incoming_message.ParseFromString(server_response)
                        return incoming_message
        except:
                return None
                print "ERROR ! Socket exception in send_message_Protobuf while sending message to " + str(ip) + " " + str(port_num)
