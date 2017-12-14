# Cassendra-type-Distributed-NoSQL-database
A cassendra type Eventually Consistent Key-Value Store 
borrows most of its designs from Cassandra and some from Dynamo.

## Requirenments

- Python 2.7
- Google's protocol buffer

## Key-Value store

Each replica server will be a key-value store. Keys are unsigned integers between 0 and 255. Values are strings.
Each replica server should support the following key-value operations:
- get key – given a key, return its corresponding value
- put key value – if the key does not already exist, create a new key-value pair; otherwise, update the key to
the new value
As with Cassandra, to handle a write request, the replica must first log this write in a write-ahead log on
persistent storage before updating its in-memory data structure. In this way, if a replica failed and restarted, it can
restore its memory state by replaying the disk log.

## Eventual Consistency

Each replica server is pre-configured with information
about all other replicas. The replication factor will be 4 – every key-value pair should be stored on all four replicas.
Every client request (get or put) is handled by a coordinator. Client can select any replica server as the coordi-
nator. 

- **Consistency level** - Similar to Cassandra, consistency level is configured by the client. When issuing a request,
put or get, the client explicitly specifies the desired consistency level: ONE or TWO. 
  - write request : For a write request with consistency level TWO, the coordinator will send the request to all replicas (including itself). 
It will respond successful to the client once the write has been written to two replicas. 
  - read request : For a read request with consistency level TWO, the coordinator will return the most recent data from two replicas. 
To support this operation, when 1handling a write request, the coordinator will record
the time at which the request was received and include this
as a timestamp when contacting replica servers for writing.

With eventual consistency, different replicas may be inconsistent. For example, due to failure, a replica misses
one write for a key k. When it recovers, it replays its log to restore its memory state. When a read request for key
k comes next, it returns its own version of the value, which is inconsistent. To ensure that all replicas eventually
become consistent, we will implement the following two procedures, and your key-value store will be configured
to use either of the two.

  - **Read repair**. When handling read requests, the coordinator contacts all replicas. If it finds inconsistent data, it will
perform “read repair” in the background.
  - **Hinted handoff** During write, the coordinator tries to write to all replicas. As long as enough replicas have
succeeded, ONE or TWO, it will respond successful to the client. However, if not all replicas succeeded, e.g., three
have succeeded but one replica server has failed, the coordinator would store a “hint” locally. If at a later time the
failed server has recovered, it might be selected as coordinator for another client’s request. This will allow other
replica servers that have stored “hints” for it to know it has recovered and send over the stored hints.

A co-ordinator is configured to use either **Hinted handoff** or **Read Repair**

To start a co-ordinator in Hinted handoff

```
python KVCoordinator.py nodename PORTNUM replicas.txt HINTED-HANDOFF

```
To start a co-ordinator in Read Repair 

```
python KVCoordinator.py nodename PORTNUM replicas.txt READ-REPAIR

```


For example, if four co-ordinator's with names: “node1”, “node2”, “node3”, and “node4” are running on
128.226.180.167 port 9090, 9091, 9092, and 9093, then replicas.txt should contain:

```
node1 128.226.180.167 9090
node2 128.226.180.167 9091
node3 128.226.180.167 9092
node4 128.226.180.167 9093
```


## Client
Once started,
the client will act as a console, allowing users to issue a stream of requests. The client selects one replica server
as the coordinator for all its requests. That is, all requests from a single client are handled by the same coordinator.
The key value store is configured to launch multiple clients, potentially issue requests to different coordinators at the same time.


To start a client 

If the client wants to select a node running on 128.226.180.167 and port 9090 as its co-ordinator 

```
python KVclient.py  128.226.180.167 9090

```

Client can issue get and put request's to co-ordinator

## Message Transfer 

File keyvalue.proto defines the messages to be transmitted among co-ordinator's and from client's in protocol buffer

```
protoc --python_out=./ keyvalue.proto
```

## DataFlow

![alt text](https://github.com/deshpandekartik/Cassendra-type-Distributed-NoSQL-database/blob/master/controlflow.png)

### Contributors:
- [Kartik Deshpande](https://www.linkedin.com/in/kartik-deshpande/)
- [Vipul Chaskar](https://www.linkedin.com/in/vipul-chaskar-50808757/)
- [Ashish Kenjale](https://www.linkedin.com/in/ashish-kenjale/)


## References
- Cassendra 
  - http://cassandra.apache.org/ 
  - https://www.facebook.com/notes/facebook-engineering/cassandra-a-structured-storage-system-on-a-p2p-network/24413138919/
- Dynamo: Amazon’s Highly Available Key-value Store Giuseppe DeCandia, Deniz Hastorun, Madan Jampani, Gunavardhan Kakulapati, Avinash Lakshman, Alex Pilchin, Swaminathan Sivasubramanian, Peter Vosshall and Werner Vogels
- Protobuf https://developers.google.com/protocol-buffers/
