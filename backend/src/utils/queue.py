from redis import Redis
from ..config.settings import REDIS_URL
QUEUE="probe-agreement:runs"
def client(): return Redis.from_url(REDIS_URL,decode_responses=True)
def enqueue(run_id): client().rpush(QUEUE,run_id)
