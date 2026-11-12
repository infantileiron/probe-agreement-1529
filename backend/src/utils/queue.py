from redis import Redis
from ..config.settings import REDIS_URL
QUEUE="probe-agreement:runs"
def client(): return Redis.from_url(REDIS_URL,decode_responses=True)
def enqueue(run_id): client().rpush(QUEUE,run_id)
def queued_ids():
 """当前仍在 Redis 信号队列中的运行 id（用于去重补发）。"""
 raw=client().lrange(QUEUE,0,-1)
 return set(raw or [])
