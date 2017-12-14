# Cassendra-type-Distributed-NoSQL-database
A cassendra type Eventually Consistent Key-Value Store 

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
