

from celery import Celery


redis_host = "RedisJobs.redis.cache.windows.net"
redis_port = 6379
redis_password = "N9xQ3tTNBV93D9NgmOaNK4WTg9wSDJbAFAzCaObWclw="


redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/0"

celery_app = Celery(
    "cl_tasks",
    broker=redis_url,
    backend=redis_url
)


@celery_app.task
def upload_files(x, y):
    return x + y