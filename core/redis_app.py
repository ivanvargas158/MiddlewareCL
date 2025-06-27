import threading
import redis
from rq import Queue
import ssl
import time
from core.settings import Redis_Port, Redis_Host, Redis_Key
from rq import Worker, Queue

# Connect to Azure Redis
redis_client = redis.Redis(
    host=Redis_Host,
    port=6380,
    password=Redis_Key,
    ssl=True,
    ssl_cert_reqs=ssl.CERT_NONE
)

redis_queue = Queue(connection=redis_client)
 
 