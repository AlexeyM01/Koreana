"""
app/api/translate.py
"""
import requests
import logging
from fastapi import APIRouter, HTTPException, status, Request, Depends
from typing import List

from app.core.config import settings
from app.core.rate_limiter import limiter
import redis.asyncio as redis
from app.core.database import get_redis

import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/translate")


@router.post("/")
@limiter.limit("30/minute")
async def translate(request: Request, text: str | List[str],
                    source_language_code: str = 'ko', target_language_code: str = 'ru',
                    redis_client: redis.Redis = Depends(get_redis)):
    try:
        if isinstance(text, str):
            text = [text]

        cache_key = f"translate:{source_language_code}:{target_language_code}:{text}"
        cached_result = await redis_client.get(cache_key)
        if cached_result:
            logger.debug(f"Translation found in cache for key: {cache_key}")
            return json.loads(cached_result)

        body = {
            "sourceLanguageCode": source_language_code,
            "targetLanguageCode": target_language_code,
            "texts": text,
            "folderId": settings.yandex_translate_folder_id,
        }
        headers = {
            "Content-Type": "application/json",
            # Параметры для аутентификации с помощью API-ключа от имени сервисного аккаунта:
            "Authorization": "Api-Key {0}".format(settings.yandex_translate_api_key),
        }
        response = requests.post(
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            json=body,
            headers=headers,
        )

        response.raise_for_status()
        data = response.json()
        translated_texts = [item["text"] for item in data["translations"]]
        logger.debug(
            f"Текст успешно переведен. Исходный язык: {source_language_code}, целевой язык: {target_language_code}")
        await redis_client.set(cache_key, json.dumps(translated_texts), ex=60 * 60 * 24)  # Храним в кэше 24 часа
        logger.debug(f"Перевод сохранен в кэше для ключа: {cache_key}")
        return translated_texts
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при обращении к API перевода: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Ошибка при обращении к сервису перевода")
    except Exception as e:
        logger.exception(f"Ошибка перевода: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Произошла ошибка перевода")
