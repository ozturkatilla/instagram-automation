from redis import Redis
from app.config import get_settings

settings = get_settings()

def get_redis_connection() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)