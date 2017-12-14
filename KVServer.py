#!/usr/bin/python

import os
import time
import sys
import SocketServer
import socket
from threading import Lock,Thread

from KVCoordinator import *

sys.path.append('/home/phao3/protobuf/protobuf-3.4.0/python')
import keyvalue_pb2


if __name__ == '__main__':
        
	if len(sys.argv) != 5:
                print "Invalid Parameters: <Node_ID> <Port> <Filename- replicas.txt> < CONSISTENCY_TYPE : READ-REPAIR / HINTED-HANDOFF >"
                sys.exit(0)
        else:
                NodeName = sys.argv[1]
                PORT = sys.argv[2]
                HOST = socket.gethostbyname(socket.gethostname())
                REPLICAFILE = sys.argv[3]
		CONSISTENCY_TYPE = sys.argv[4]


        replica_list = {}
        # parse replica file ( data of all other replicas in n/w )
        if not os.path.exists(REPLICAFILE):
                print "ERROR ! Input file not found"
                sys.exit(0)
        else:
                try:
                        with open(REPLICAFILE) as file:
                                for line in file:
                                        data = line.split(' ')
                                        if data[0].rstrip() == NodeName and data[1].rstrip() == HOST and data[2].rstrip() == PORT :
                                                # don't add self node in list
                                                pass
                                        else:
                                                replica_list[data[0].rstrip()] = [ data[1].rstrip() , data[2].rstrip() ]
                except:
                        print "ERROR ! Not able to read input file, please check the format"
			sys.exit(0)


        print('Starting Controller ' + NodeName + ' on ' + str(HOST) + ':' + str(PORT) + '...')


        try:
                server = MyServer((HOST, int(PORT)), KVCoordinator, NodeName , HOST ,PORT, replica_list, CONSISTENCY_TYPE)
                server.serve_forever()
                pass
        except:
                print "EXCEPTION ! socket exception on port."
                sys.exit(0)

