""" Используется для взаимодействия с Redis.
Реализует функции для получения и установки задач в кэш.
Асинхронная работа с Redis, что позволяет избежать блокировок в процессе обработки запросов.
"""
import redis

from config import settings

redis = redis.from_url(settings.redis_url, decode_responses=True)


async def get_task_from_cache(task_id: int):
    """Достаем задачу из кэша"""
    task = await redis.get(f"task:{task_id}")
    if task:
        return task
    return None


async def set_task_in_cache(task_id: int, task_data):
    """Сохраняем задачу в кэш"""
    await redis.set(f"task:{task_id}", task_data)


async def set_token_in_cache(username: str, token: str, expire_minutes: int):
    """Сохраняет JWT токен в Redis."""
    await redis.set(f"token:{username}", token, ex=expire_minutes * 60)
