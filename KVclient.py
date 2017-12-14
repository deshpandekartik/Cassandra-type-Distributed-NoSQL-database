#!/usr/bin/python

import os
import time
import sys
import socket
import re

from SocketPool import SocketPool
import keyvalue_pb2

MAX_REQUEST_SIZE = 10000

class ClientHandler:

	HOST = None
	Port = None
	socketpool = SocketPool()

	def __init__(self, host, port):
		self.HOST = host
		self.PORT = port

	def send_get_request(self , key, consistency):
		
		# Start marshalling get request message
		get_request_msg = keyvalue_pb2.GetRequest()
		get_request_msg.id = 10000
		get_request_msg.key = key
		get_request_msg.consistency_level = consistency

		final_message = keyvalue_pb2.KeyValueMessage()
		final_message.getrequest.CopyFrom(get_request_msg)
		encoded = final_message.SerializeToString()

		# Send the packed message to coordinator
		return_message = self.socketpool.send_message_Protobuf(self.HOST, self.PORT, encoded)
		#print return_message

		if return_message == None:
			return "(Error): Got no response from server."
		else:
			if return_message.clientresponse.status == True:
				# key found at server end

				# return value for key
				return "(Success): " + str(return_message.clientresponse.value)
			else:
				# key not present at server
				if return_message.clientresponse.value.strip() == "Consistency":
					return "(Error): Consistency level not met."
				else:
					return "(Error): Key not present."


	def send_put_request(self , key, value, consistency):

                # Start marshalling get request message
                put_request_msg = keyvalue_pb2.PutRequest()
                put_request_msg.id = 10000
                put_request_msg.key = key
		put_request_msg.value = value
                put_request_msg.consistency_level = consistency

                final_message = keyvalue_pb2.KeyValueMessage()
                final_message.putrequest.CopyFrom(put_request_msg)
                encoded = final_message.SerializeToString()

                # Send the packed message to coordinator
                return_message = self.socketpool.send_message_Protobuf(self.HOST, self.PORT, encoded)
		#print return_message

                if return_message == None:
                        return "(Error): Got no response from server."
                else:
			if return_message.clientresponse.status == True:
				return "(Success): Key inserted."
			else:
				if return_message.clientresponse.value.strip() == "Consistency":
                       			return "(Error): Consistency level not met."
                     		else:
                        	     	return "(Error): Key insertion failed."


if len(sys.argv) != 3:
        print "Invalid Parameters: <Replica IP> <Replica Port>"
        sys.exit(0)
else:
        HOST = sys.argv[1]
        PORT = sys.argv[2]

obj = ClientHandler(HOST,PORT)

print "Connected to replica " + str(HOST) + ":" + str(PORT)
print "\nAvailable commands:"
print "PUT <consistency_level> <key> <value>	(Ex. PUT 2 12 'Hey there')"
print "GET <consistency_level> <key> <value>	(Ex. GET 2 12)"
print "EXIT"

# console for user input
while True:

	rawuserinput = raw_input("\nPlease enter one of the above commands:\n")

	if rawuserinput != "" :
		userinput = rawuserinput.split()
	        if userinput[0] == "GET":
        	        try:
                	        key = int(userinput[2])
                	        consistency = int(userinput[1])
				print "Replica Response " + str(obj.send_get_request(key,consistency))
                	except:
                	        print "ERROR! Invalid GET command."

	        elif userinput[0] == "PUT":
			try:
        	                key = int(userinput[2])
        	                value = re.search('[\'"](.*)[\'"]', rawuserinput).group(1)
        	                consistency = int(userinput[1])
				print "Replica Response " + str(obj.send_put_request(key,value,consistency))
			except:
				print "ERROR! Invalid PUT command."
        	elif userinput[0] == "EXIT":
			sys.exit(0)
		else:
                	print "ERROR! Invalid command entered."

