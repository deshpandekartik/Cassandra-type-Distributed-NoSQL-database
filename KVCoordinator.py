#!/usr/bin/python

import os
import time
import sys
import SocketServer
import socket
from threading import Lock,Thread

from KVStore import KVStore
from KVConsistency import KVConsistency
from SocketPool import SocketPool

sys.path.append('/home/phao3/protobuf/protobuf-3.4.0/python')
import keyvalue_pb2

class MyServer(SocketServer.ThreadingTCPServer):
        def __init__(self, server_address, RequestHandlerClass, nodename ,hostip , hostport , completereplicalist , consistencymethod):
		SocketServer.ThreadingTCPServer.__init__(self,server_address,RequestHandlerClass)
                self.nodename = nodename
                self.host = hostip
                self.port = hostport
                self.replicalist = completereplicalist
		self.consistency_type = consistencymethod

MAX_REQUEST_SIZE = 10000
class KVCoordinator(SocketServer.BaseRequestHandler):
    	HOST = None
    	PORT = None
   	replica_list = {}
    	CONSISTENCTY_TYPE = None
	kvstore = KVStore()
	kvconsistency = KVConsistency(kvstore)
	READ_REPAIR = "READ-REPAIR"
	HINTED_HANDOFF = "HINTED-HANDOFF"
	socketpool = SocketPool()

    	def handle(self):
	   	# Current node ID
        	self.node_id = str(self.server.nodename)
        	self.HOST = self.server.host
        	self.PORT = self.server.port
        	self.replica_list = self.server.replicalist
		self.CONSISTENCTY_TYPE = self.server.consistency_type

                # if KV dict not initialized , initialize it
                if self.kvstore.initialization_status == False:
                        self.kvstore.initialize(self.node_id)

		# if KVConsitency not initialized, initialize it
		if self.kvconsistency.initialization_status == False:
                        self.kvconsistency.initialize(self.node_id, self.kvstore)

        	# handle incoming socket requests from other servers / clients
        	message = self.request.recv(MAX_REQUEST_SIZE)
        	incoming_message = keyvalue_pb2.KeyValueMessage()
        	incoming_message.ParseFromString(message)

        	print incoming_message

        	if incoming_message.HasField("putrequest") :
        	        self.handle_put_request_from_client(incoming_message)
        	elif incoming_message.HasField("getrequest") :
        	        # request from client ,return val for a key
        	        self.handle_get_request_from_client(incoming_message)
        	elif incoming_message.HasField("clientresponse") :
        	        pass
        	elif incoming_message.HasField("putrequestsrv") :
        	        self.handle_put_request_from_server(incoming_message)
        	elif incoming_message.HasField("getrequestsrv") :
        	        self.handle_get_request_from_server(incoming_message)
        	elif incoming_message.HasField("serverresponse") :
        	        pass
        	elif incoming_message.HasField("readrepair") :
        	        pass


    	def handle_get_request_from_client(self, incoming_message):

		# unpack the message
       		Id = incoming_message.getrequest.id
     		Key = incoming_message.getrequest.key
     		Consistency = incoming_message.getrequest.consistency_level

       		# get value for corresponding key
    		return_val = self.get_value_from_client(Key,Consistency)

      		# Start packing response to client
     		client_response_message = keyvalue_pb2.ClientResponse()
    		client_response_message.id = Id
    		client_response_message.key = Key


     		if return_val == None or return_val == False:
			if return_val == False:
      				# key not found in local memory
        	     		client_response_message.status = False
        	   		client_response_message.value = "None"
			else:
				# key not found in local memory
                                client_response_message.status = False
                                client_response_message.value = "Consistency"
    		else:
        	   	# key present in local memory
        	     	client_response_message.status = True
        	   	client_response_message.value = return_val
	
	     	response_message = keyvalue_pb2.KeyValueMessage()
	   	response_message.clientresponse.CopyFrom(client_response_message)
	   	encodedmessage = response_message.SerializeToString()

    		try:
      			# send response to client
        	     	self.request.send(encodedmessage)
      		except:
        	    	print "ERROR ! socket exception while sending get val response to client"

	def handle_put_request_from_client(self, incoming_message):

                # request from client to put a key value pair in local memory

                # unpack the message
                Id = incoming_message.putrequest.id
                Key = incoming_message.putrequest.key
                Value = incoming_message.putrequest.value
                Consistency = incoming_message.putrequest.consistency_level

                # insert key val pair in local memory
                return_val = self.set_from_client(Key, Value, int(time.time()),Consistency)

                # Start packing response to client
                client_response_message = keyvalue_pb2.ClientResponse()
                client_response_message.id = Id
                client_response_message.key = Key

                if return_val == False or return_val == None:
			if return_val == False:
	                        # Not able to insert key in local memory
        	                client_response_message.status = False
                	        client_response_message.value = "None"
			else:
				client_response_message.status = False
                                client_response_message.value = "Consistency"
                else:
                        # key inserted successfully
                        client_response_message.status = True
                        client_response_message.value = "None"

                response_message = keyvalue_pb2.KeyValueMessage()
                response_message.clientresponse.CopyFrom(client_response_message)
                encodedmessage = response_message.SerializeToString()
                try:
                        # send acknowledgement to client
                        self.request.send(encodedmessage)
                except:
                        print "ERROR ! socket exception while sending put val response to client"


	def handle_get_request_from_server(self,incoming_message):
                # unpack the message
                Id = incoming_message.getrequestsrv.id
                Key = incoming_message.getrequestsrv.key
                Timestamp = incoming_message.getrequestsrv.timestamp

                # get value for corresponding key
                return_val = self.get_value_from_server(Key)

                # Start packing response to server
                server_response_message = keyvalue_pb2.ServerResponse()
                server_response_message.id = Id
                server_response_message.key = Key
                server_response_message.nodeid = self.node_id

                if return_val == None or return_val == False:
                        # key not found in local memory
                        server_response_message.status = False
                        server_response_message.value = "None"
                        server_response_message.timestamp = 0
                else:
                        # key present in local memory
                        server_response_message.status = True
                        server_response_message.value = return_val
                        server_response_message.timestamp = self.kvstore.get_timestamp(Key)

                response_message = keyvalue_pb2.KeyValueMessage()
                response_message.serverresponse.CopyFrom(server_response_message)
                encodedmessage = response_message.SerializeToString()

                try:
                        # send response to client
                        self.request.send(encodedmessage)
                except:
                        print "ERROR ! socket exception while sending get val response to server"



	def handle_put_request_from_server(self,incoming_message):
                # unpack the message
                Id = incoming_message.putrequestsrv.id
                Key = incoming_message.putrequestsrv.key
                Value = incoming_message.putrequestsrv.value
                timestamp = incoming_message.putrequestsrv.timestamp


                # insert key val pair in local memory
                return_val = self.set_from_server(Key, Value, timestamp)

                # Start packing response
                server_response_message = keyvalue_pb2.ServerResponse()
                server_response_message.id = Id
                server_response_message.key = Key
                server_response_message.value = "None"
                server_response_message.timestamp = timestamp

                if return_val == False or return_val == None:
                        # Not able to insert key in local memory
                        server_response_message.status = False
                else:
                        # key inserted successfully
                        server_response_message.status = True

                response_message = keyvalue_pb2.KeyValueMessage()
                response_message.serverresponse.CopyFrom(server_response_message)
                encodedmessage = response_message.SerializeToString()

                try:
                        # send acknowledgement to client
                        self.request.send(encodedmessage)
                except:
                        print "ERROR ! socket exception while sending put val response to client"



	################################################
	# Return val
	# True - Key retrived success
	# False - Key not present
	# None - Key present, but consistency not met
	################################################
	def get_value_from_client(self,key,Consistency):

		value = self.kvstore.get_value(key)

		if Consistency == 1:
			return value

		if value == None or value == False:
			# key not present in local memory , further check if key present on other replicas
	                timestamp = 0
		else:
			# key present in local memory
			timestamp = self.kvstore.get_timestamp(key)
	

		# pack the message to contact all server to get value associated with key
	        # response will be returned only if timestamp of their key is greater then timestamp associated with this key
        	get_requestsrv_message = keyvalue_pb2.GetRequestSrv()
        	get_requestsrv_message.id = 1   # random id for now
        	get_requestsrv_message.key = key
        	get_requestsrv_message.timestamp = timestamp

        	forward_message = keyvalue_pb2.KeyValueMessage()
        	forward_message.getrequestsrv.CopyFrom(get_requestsrv_message)
        	encodedmessage = forward_message.SerializeToString()

        	LatestNode = None
        	LatestValue = None
        	LatestTimestamp = timestamp
        	read_repair_list = {}

		server_contacted = 1 	# counter to check for no of servers contacted to maintain consistency
        	flag = False
        	# contact all replicas and get the value and timestamp for corresponding key
	        for nodeid in self.replica_list:

        	        nexthost = self.replica_list[nodeid][0]
                	nextport = self.replica_list[nodeid][1]

                	# SEND packed message to all coordinators in N/W
                	return_message = self.socketpool.send_message_Protobuf(nexthost,nextport,encodedmessage)

                	# creae the read repair list
                	if return_message != None:
				server_contacted = server_contacted + 1
                	        read_repair_list[nodeid] = return_message.serverresponse.timestamp
                	else:
                	        read_repair_list[nodeid] = 0

                	if return_message != None and return_message.serverresponse.status == True and return_message.serverresponse.timestamp > LatestTimestamp:
                	        flag = True
                	        LatestNode = nodeid
                	        LatestValue = return_message.serverresponse.value
                	        LatestTimestamp = return_message.serverresponse.timestamp

        	dictkeys = read_repair_list.keys()
        	for nodeid in dictkeys:
                	if int(read_repair_list[nodeid]) == LatestTimestamp:
                        	# remove all up to date nodes from read repair list
                        	del read_repair_list[nodeid]

        	if LatestValue != None:
                	# first perform read repair locally
                	self.set_from_server(key, LatestValue, LatestTimestamp)



		# check if CONSISTENCTY_TYPE is read repair
                if self.CONSISTENCTY_TYPE == self.READ_REPAIR:
	        	# call read repair func to perform read repair on all outdated servers
        		thread = Thread(target = self.kvconsistency.perform_read_repair, args=(key,read_repair_list,self.replica_list,))
        		thread.daemon = True
        		thread.start()

		if server_contacted < Consistency:
			# Consistency requirenment not met
			return None

		if flag == False:
			return value
		else:
	        	return LatestValue


        ################################################
        # Return val
        # True - Key insertion success
        # False - Key insertion failure
        # None - Key inserted to all active servers but consistency not met
        ################################################
	def set_from_client(self,key,value,timestamp,consistency):

		# pack the message to replicate on other servers
        	put_requestsrv_message = keyvalue_pb2.PutRequestSrv()
        	put_requestsrv_message.id = 1   # random id for now
        	put_requestsrv_message.key = key
        	put_requestsrv_message.value = value
        	put_requestsrv_message.timestamp = timestamp
	
        	forward_message = keyvalue_pb2.KeyValueMessage()
        	forward_message.putrequestsrv.CopyFrom(put_requestsrv_message)
        	encodedmessage = forward_message.SerializeToString()

		failed_nodes = []
        	replica_success_count = 1       # mainitaining no of success responses
        	# now replicate this pair to all other servers, and get response
        	for nodeid in self.replica_list:
                	nexthost = self.replica_list[nodeid][0]
                	nextport = self.replica_list[nodeid][1]

               		# SEND packed message to all coordinators in N/W
                	return_message = self.socketpool.send_message_Protobuf(nexthost,nextport,encodedmessage)

                	if return_message != None and return_message.serverresponse.status == True:
                        	# key, value pair updated/inserted on server
                        	replica_success_count = replica_success_count + 1
                	else:
				failed_nodes.append(nodeid)			

	        if self.CONSISTENCTY_TYPE == self.HINTED_HANDOFF:
        	    if self.kvconsistency.hinted_handoff_daemon_status == False:
        	        thread = Thread(target = self.kvconsistency.send_hinted_handoffmsgs, args=(self.replica_list,))
        	        thread.daemon = True
        	        thread.start()

        	# if succesfully written to servers based on consistency return true else false
        	if replica_success_count >= consistency:
			for nodeid in failed_nodes:
				with self.kvconsistency.hinted_handoff_lock:
					if nodeid in self.kvconsistency.hinted_handoff:
						# insert key if not present
                	                    	if key not in self.kvconsistency.hinted_handoff[nodeid]:
                	                      		self.kvconsistency.hinted_handoff[nodeid].append(key)
                	          	else:
                	                 	self.kvconsistency.hinted_handoff[nodeid] = [ key ]
				
			self.kvstore.set(key,value,timestamp)
        	        return True
        	else:
        	        return None


        ################################################
        # Return val
        # True - Key insertion success
        # False - Key insertion failure
        ################################################
	def get_value_from_server(self,key):
		value = self.kvstore.get_value(key)
		return value

        ################################################
        # Return val
        # True - Key insertion success
        # False - Key insertion failure
        ################################################
	def set_from_server(self,key,value,timestamp):
		retval = self.kvstore.set(key,value,timestamp)
		return retval

