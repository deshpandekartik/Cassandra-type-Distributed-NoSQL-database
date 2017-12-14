#!/usr/bin/python

import os
import time
import sys
import SocketServer
from threading import Lock,Thread
import socket
import keyvalue_pb2

class KVStore:
    kv_dict = {}
    LOG_FILE_FORMAT = "writelog_"
    MIN_KEY_VALUE = 0
    MAX_KEY_VALUE = 255
    VALUE_POSITION = 0
    TIMESTAMP_POSITION = 1
    kv_dict_lock = Lock()
    initialization_status = False
    DIR = "logs"

    def initialize(self,node_name):

	self.initialization_status = True
	# Current node ID
        self.node_id = node_name
        self.log_file_name = self.DIR + "/" + self.LOG_FILE_FORMAT + "_" + self.node_id

	if not os.path.exists(self.DIR):
		os.makedirs(self.DIR)

        if os.path.exists(self.log_file_name):

            # Populate the in-memory key-value store from log file
            log_file_handle = open(self.log_file_name, "r")
            for line in log_file_handle:
                a_line = line.split('::')
                self.set(int(a_line[0]), a_line[1], int(a_line[2]), False)
                # Last argument is set to false since we're already reading from log file here and we don't again
                # want to write these key-values to log file inside set() (write_log_log = False)

        else:
            # Just create the log file
            log_file_handle = open(self.log_file_name, "w+")

        log_file_handle.close()


    def get(self, key):

        if key not in self.kv_dict:
            return False

        return self.kv_dict[key]

    def get_value(self, key):

        if key not in self.kv_dict:
            return False

        return self.kv_dict[key][self.VALUE_POSITION]

    def get_timestamp(self, key):

        if key not in self.kv_dict:
            return False

        return self.kv_dict[key][self.TIMESTAMP_POSITION]

    def set(self, key, value, timestamp, write_to_log=True):
        if key < self.MIN_KEY_VALUE or key > self.MAX_KEY_VALUE:
            print "ERROR! Unsupported key " + str(key) + " given."
            return False

	# check if key already in dict
	if self.get(key) != None and self.get(key) != False:
		if self.get_timestamp(key) > timestamp:
			return True


        # Write to log file first
        if write_to_log:
            try:
                log_file_handle = open(self.log_file_name, "a")
                log_file_handle.write(str(key) + "::" + value + "::" + str(timestamp) + "\n")
                log_file_handle.close()
            except IOError:
                print "ERROR! The log file " + self.log_file_name + " was not found!"
                return False

	# critical section , kv_dict can be called upon multiple requests
	with self.kv_dict_lock:
	        # Then write to in-memory key-value store
        	self.kv_dict[key] = []
        	self.kv_dict[key].insert(self.VALUE_POSITION, value)
        	self.kv_dict[key].insert(self.TIMESTAMP_POSITION, timestamp)

        return True

    def clear(self):
        self.kv_dict = {}

        try:
            log_file_handle = open(self.log_file_name, "w+")
            log_file_handle.close()
        except IOError:
            print "WARNING! Unable to open " + self.log_file_name + "."



