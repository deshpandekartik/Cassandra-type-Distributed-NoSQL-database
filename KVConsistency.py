#!/usr/bin/python

import os
import time
import sys
import SocketServer
import socket
from threading import Lock,Thread

from KVStore import KVStore
from SocketPool import SocketPool

import keyvalue_pb2



class KVConsistency:

    hinted_handoff_lock = Lock()
    hinted_handoff_daemon_status = False
    #kvstore = KVStore()
    socketpool = SocketPool()  
    hinted_handoff = {} 
    HOST_POSITION = 0
    PORT_POSITION = 1
    initialization_status = False

    def __init__(self, kvstore):
        self.kvstore = kvstore

    def initialize(self,node_name,kvstore):
        self.initialization_status = True
        # Current node ID
        self.node_id = node_name
	self.kvstore = kvstore

    # will run as a daemon thread, infinite loop
    def send_hinted_handoffmsgs(self,replica_list):
        while True:
                dictkeys = self.hinted_handoff.keys()
                for nodeid in dictkeys:
                        self.hinted_handoff_daemon_status = True
                        for key in self.hinted_handoff[nodeid]:
                                # print " Getting key " + str(key) + " from object " + str(self.kvstore)
                                value = self.kvstore.get_value(key)
                                timestamp = self.kvstore.get_timestamp(key)

                                # pack the message to replicate on other servers
                                put_requestsrv_message = keyvalue_pb2.PutRequestSrv()
                                put_requestsrv_message.id = 1   # random id for now
                                put_requestsrv_message.key = key
                                put_requestsrv_message.value = value
                                put_requestsrv_message.timestamp = timestamp

                                forward_message = keyvalue_pb2.KeyValueMessage()
                                forward_message.putrequestsrv.CopyFrom(put_requestsrv_message)
                                encodedmessage = forward_message.SerializeToString()


                                nexthost = replica_list[nodeid][self.HOST_POSITION]
                                nextport = replica_list[nodeid][self.PORT_POSITION]

                                return_message = self.socketpool.send_message_Protobuf(nexthost,nextport,encodedmessage)

                                if return_message != None and return_message.serverresponse.status == True:

                                        # entering critical section
                                        with self.hinted_handoff_lock:
                                                # key value updated to server,remove key from hinted handoff
                                                self.hinted_handoff[nodeid].remove(key)

                                                if len(self.hinted_handoff[nodeid]) == 0:
                                                        del self.hinted_handoff[nodeid]
                                else:
                                        # updating of key value failed , do nothing
                                        pass

                        # sleep needed while implementing locks for critical section
                        time.sleep(4)

    #will run as a daemon thread
    def perform_read_repair(self , key, read_repair_list,replica_list):
                for nodeid in read_repair_list:
			value = self.kvstore.get_value(key)
                    	timestamp = self.kvstore.get_timestamp(key)

                        # pack the message to replicate on other servers
                        put_requestsrv_message = keyvalue_pb2.PutRequestSrv()
                        put_requestsrv_message.id = 1   # random id for now
                        put_requestsrv_message.key = key
                        put_requestsrv_message.value = value
                        put_requestsrv_message.timestamp = timestamp

                        forward_message = keyvalue_pb2.KeyValueMessage()
                        forward_message.putrequestsrv.CopyFrom(put_requestsrv_message)
                        encodedmessage = forward_message.SerializeToString()

                        nexthost = replica_list[nodeid][self.HOST_POSITION]
                        nextport = replica_list[nodeid][self.PORT_POSITION]

                        return_message = self.socketpool.send_message_Protobuf(nexthost,nextport,encodedmessage)

