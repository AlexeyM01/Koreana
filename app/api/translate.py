import requests
from fastapi import APIRouter, HTTPException, status
from typing import List

from app.core.config import settings

router = APIRouter(prefix="/translate")
texts = ["I want to translate long text cause", "I don't want to translate Hello World"]


@router.post("/")
def translate(text: str | List[str], source_language_code: str = 'ko', target_language_code: str = 'ru'):
    if isinstance(text, str):
        text = [text]
        print(text)
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
    try:
        response = requests.post(
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            json=body,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        translated_texts = [item["text"] for item in data["translations"]]
        return translated_texts
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail=f"Ошибка при обращении к Yandex Translate API: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Внутренняя ошибка сервера: {e}")
